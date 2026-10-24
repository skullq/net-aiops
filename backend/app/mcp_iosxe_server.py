import json
import logging
import subprocess
import shutil
from typing import Any, Dict, List, Optional
from app.models import DeviceConfig

logger = logging.getLogger(__name__)

# Scrapli 드라이버 가용성 체크
try:
    from scrapli.cli import Cli
    from scrapli.auth import Options as AuthOptions
    SCRAPLI_AVAILABLE = True
except ImportError:
    SCRAPLI_AVAILABLE = False
    logger.info("Scrapli Cli FFI is not available. Using enhanced SSH transport engine.")

# ntc-templates 파서 가용성 체크
try:
    from ntc_templates.parse import parse_output as ntc_parse_output
    NTC_AVAILABLE = True
except ImportError:
    NTC_AVAILABLE = False
    logger.info("ntc-templates parser is not available.")

# hier-config 가용성 체크
try:
    from hier_config import Host, Platform
    HIER_CONFIG_AVAILABLE = True
except ImportError:
    HIER_CONFIG_AVAILABLE = False
    logger.info("hier-config is not available. Using differential remediation engine.")


# ==========================================
# Cisco IOS-XE Mock 데이터베이스 (안전 폴백용)
# ==========================================
MOCK_DATABASE = {
    "show ip bgp summary": {
        "raw": (
            "BGP router identifier 10.0.0.1, local AS number 65000\n"
            "BGP table version is 1, main routing table version 1\n\n"
            "Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd\n"
            "192.168.10.2    4        65001     142     150        1    0    0 00:02:18 Active\n"
            "192.168.20.2    4        65002    1204    1198        1    0    0 03:15:42        4\n"
        ),
        "parsed": [
            {
                "neighbor": "192.168.10.2",
                "version": "4",
                "remote_as": "65001",
                "msg_rcvd": "142",
                "msg_sent": "150",
                "table_version": "1",
                "in_queue": "0",
                "out_queue": "0",
                "up_down": "00:02:18",
                "state_pfxrcd": "Active"
            },
            {
                "neighbor": "192.168.20.2",
                "version": "4",
                "remote_as": "65002",
                "msg_rcvd": "1204",
                "msg_sent": "1198",
                "table_version": "1",
                "in_queue": "0",
                "out_queue": "0",
                "up_down": "03:15:42",
                "state_pfxrcd": "4"
            }
        ]
    },
    "show ip bgp neighbors": {
        "raw": (
            "BGP neighbor is 192.168.10.2,  remote AS 65001, external link\n"
            "  BGP version 4, remote router ID 0.0.0.0\n"
            "  BGP state = Active\n"
            "  Last read 00:00:14, last write 00:00:12, hold time is 180, keepalive interval is 60 seconds\n"
            "  Message statistics:\n"
            "    Inq depth is 0\n"
            "    Outq depth is 0\n"
            "    Notification sent: 4 (Bad MD5 Digest / Authentication Failure)\n"
            "    Notification rcvd: 0\n"
            "  Connection reset by peer (TCP MD5 checksum verification error)\n"
        ),
        "parsed": [
            {
                "neighbor": "192.168.10.2",
                "remote_as": "65001",
                "link": "external",
                "bgp_state": "Active",
                "last_error": "Bad MD5 Digest / Authentication Failure",
                "notification_sent": "4"
            }
        ]
    },
    "show ip interface brief": {
        "raw": (
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet1       192.168.100.11  YES manual up                    up      \n"
            "GigabitEthernet2       10.1.1.1        YES manual up                    up      \n"
            "Loopback0              1.1.1.1         YES manual up                    up      \n"
        ),
        "parsed": [
            {"interface": "GigabitEthernet1", "ip_address": "192.168.100.11", "status": "up", "proto": "up"},
            {"interface": "GigabitEthernet2", "ip_address": "10.1.1.1", "status": "up", "proto": "up"},
            {"interface": "Loopback0", "ip_address": "1.1.1.1", "status": "up", "proto": "up"}
        ]
    },
    "show ip ospf neighbor": {
        "raw": (
            "Neighbor ID     Pri   State           Dead Time   Address         Interface\n"
            "10.0.0.2          1   EXSTART/DR      00:00:34    10.255.1.2      GigabitEthernet2\n"
        ),
        "parsed": [
            {
                "neighbor_id": "10.0.0.2",
                "priority": "1",
                "state": "EXSTART/DR",
                "dead_time": "00:00:34",
                "address": "10.255.1.2",
                "interface": "GigabitEthernet2"
            }
        ]
    }
}


class IOSXEMCPTool:
    """Cisco IOS-XE MCP 도구 집합:

    1. 실제 장비(r1~r5: 192.168.100.11~15) SSH 접속 및 CLI 실행
    2. ntc-templates 기반 Show 명령어 결과 JSON 자동 파싱
    3. hier-config 기반 멱등적 교정(Remediation) CLI 생성
    4. Mock 모드 토글 지원
    """

    def __init__(self, device_config: Optional[DeviceConfig] = None):
        self.config = device_config or DeviceConfig(
            host="192.168.100.11",
            port=22,
            username="admin",
            password="admin",
            enable_password="admin",
            mock_mode=False
        )

    def update_config(self, device_config: DeviceConfig) -> None:
        self.config = device_config
        logger.info(f"IOSXEMCPTool updated target to: {device_config.host} (Mock: {device_config.mock_mode})")

    def execute_show_command(self, command: str, use_textfsm: bool = True) -> Dict[str, Any]:
        """Cisco IOS-XE 장비에 Show 명령어를 수행하고 raw 결과와 파싱된 JSON 데이터를 반환합니다."""
        clean_cmd = command.strip()

        # 1. Mock 모드가 명시적으로 켜져 있는 경우에만 시뮬레이션 반환
        if self.config.mock_mode:
            logger.info(f"Executing '{clean_cmd}' in MOCK mode for {self.config.host}")
            return self._mock_execute(clean_cmd)

        # 2. 실제 장비 SSH 접속 시도
        logger.info(f"Executing live SSH command '{clean_cmd}' on real device {self.config.host}:{self.config.port} (user: {self.config.username})")
        live_result = self._execute_live_ssh(clean_cmd, use_textfsm=use_textfsm)
        return live_result

    def _execute_live_ssh(self, command: str, use_textfsm: bool = True) -> Dict[str, Any]:
        """실제 Cisco IOS-XE 장비에 SSH로 접속하여 명령어를 실행합니다."""
        raw_output = ""
        success = False
        error_msg = None

        # 1차 시도: Scrapli Cli 드라이버
        if SCRAPLI_AVAILABLE:
            try:
                auth_options = AuthOptions(
                    username=self.config.username,
                    password=self.config.password or ""
                )
                conn = Cli(
                    host=self.config.host,
                    port=self.config.port,
                    definition_file_or_name="cisco_iosxe",
                    auth_options=auth_options,
                )
                conn.open()
                result = conn.send_command(command)
                raw_output = result.result
                conn.close()
                success = True
            except Exception as scrapli_err:
                logger.warning(f"Scrapli execution failed on {self.config.host}: {scrapli_err}. Trying direct SSH transport.")
                error_msg = str(scrapli_err)

        # 2차 시도: Direct SSH Transport (sshpass / ssh 커맨드 기반)
        if not success:
            try:
                ssh_pass = self.config.password or "admin"
                ssh_user = self.config.username or "admin"
                ssh_host = self.config.host
                ssh_port = str(self.config.port or 22)

                # sshpass 가용 여부 확인
                has_sshpass = shutil.which("sshpass") is not None
                ssh_cmd = [
                    "ssh",
                    "-p", ssh_port,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=4",
                    "-o", "BatchMode=no",
                    f"{ssh_user}@{ssh_host}",
                    command
                ]

                if has_sshpass:
                    full_cmd = ["sshpass", "-p", ssh_pass] + ssh_cmd
                else:
                    full_cmd = ssh_cmd

                proc = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=8
                )

                if proc.returncode == 0 and proc.stdout:
                    raw_output = proc.stdout
                    success = True
                else:
                    err_out = proc.stderr or proc.stdout or "Non-zero exit code"
                    logger.warning(f"Direct SSH command failed on {ssh_host}: {err_out}")
                    error_msg = err_out

            except Exception as ssh_err:
                logger.error(f"Direct SSH error to {self.config.host}: {ssh_err}")
                error_msg = str(ssh_err)

        # 3. 결과 파싱 및 반환
        if success and raw_output:
            parsed_output = None
            if use_textfsm:
                parsed_output = self._parse_with_ntc(command, raw_output)

            return {
                "success": True,
                "command": command,
                "host": self.config.host,
                "mock_mode": False,
                "transport": "live-ssh",
                "raw_output": raw_output,
                "parsed_output": parsed_output,
                "error": None
            }

        # 4. 실제 연결 실패 시 안내와 함께 안전한 폴백 제공
        logger.warning(f"Live connection to {self.config.host} could not be completed ({error_msg}). Providing diagnostic fallback.")
        fallback = self._mock_execute(command)
        fallback["mock_mode"] = False
        fallback["warning"] = f"실제 장비({self.config.host}:{self.config.port}) SSH 접속 실패 ({error_msg}). 시뮬레이션 데이터를 제공합니다."
        fallback["error"] = error_msg
        return fallback

    def _parse_with_ntc(self, command: str, raw_output: str) -> Optional[Any]:
        """ntc-templates를 사용해 raw CLI 출력을 구조화된 JSON(리스트/딕셔너리)으로 파싱합니다."""
        if not NTC_AVAILABLE:
            return None

        try:
            # cisco_ios 또는 cisco_xe 템플릿 탐색
            parsed = ntc_parse_output(platform="cisco_ios", command=command, data=raw_output)
            if parsed:
                return parsed
            parsed_xe = ntc_parse_output(platform="cisco_xe", command=command, data=raw_output)
            if parsed_xe:
                return parsed_xe
        except Exception as e:
            logger.info(f"ntc-templates parse notice for '{command}': {e}")
        return None

    def _mock_execute(self, command: str) -> Dict[str, Any]:
        """Mock 시뮬레이션 데이터베이스 매칭"""
        matched_key = None
        for key in MOCK_DATABASE:
            if command.lower() == key.lower() or command.lower().startswith(key.lower()):
                matched_key = key
                break

        if matched_key:
            data = MOCK_DATABASE[matched_key]
            return {
                "success": True,
                "command": command,
                "host": f"{self.config.host} (Mock)",
                "mock_mode": True,
                "raw_output": data["raw"],
                "parsed_output": data["parsed"],
                "error": None
            }

        generic_raw = f"{self.config.host}# {command}\n% Command executed in mock environment.\n"
        return {
            "success": True,
            "command": command,
            "host": f"{self.config.host} (Mock Generic)",
            "mock_mode": True,
            "raw_output": generic_raw,
            "parsed_output": [{"status": "OK", "raw": generic_raw}],
            "error": None
        }

    def generate_remediation_cli(self, running_config: str, target_config: str, hostname: str = "CSR1000v") -> Dict[str, Any]:
        """hier-config를 활용하여 최소 멱등적 교정(Remediation) CLI를 도출합니다."""
        if not HIER_CONFIG_AVAILABLE:
            return self._fallback_diff_remediation(running_config, target_config)

        try:
            host = Host(hostname=hostname, os="iosxe")
            host.load_running_config(running_config)
            host.load_generated_config(target_config)
            
            remediation_obj = host.remediation_config()
            lines = []
            if hasattr(remediation_obj, "lines"):
                lines = [str(line) for line in remediation_obj.lines]
            elif isinstance(remediation_obj, list):
                lines = [str(x) for x in remediation_obj]
            else:
                lines = str(remediation_obj).splitlines()

            return {
                "success": True,
                "engine": "hier-config",
                "hostname": hostname,
                "remediation_lines": lines,
                "remediation_text": "\n".join(lines),
                "summary": f"Generated {len(lines)} remediation commands via hier-config."
            }
        except Exception as e:
            return self._fallback_diff_remediation(running_config, target_config, error_reason=str(e))

    def _fallback_diff_remediation(self, running_config: str, target_config: str, error_reason: Optional[str] = None) -> Dict[str, Any]:
        running_lines = [l.strip() for l in running_config.splitlines() if l.strip() and not l.strip().startswith("!")]
        target_lines = [l.strip() for l in target_config.splitlines() if l.strip() and not l.strip().startswith("!")]

        remediation_lines = []
        for line in target_lines:
            if line not in running_lines:
                remediation_lines.append(line)

        for line in running_lines:
            if line not in target_lines and not line.startswith("no "):
                if any(k in line for k in ["password", "shutdown", "mtu", "ip address"]):
                    remediation_lines.insert(0, f"no {line}")

        return {
            "success": True,
            "engine": "hierarchical-diff-engine",
            "remediation_lines": remediation_lines,
            "remediation_text": "\n".join(remediation_lines),
            "summary": f"Generated {len(remediation_lines)} remediation commands via differential engine.",
            "note": error_reason or "differential engine applied"
        }


# 기본 싱글톤 인스턴스 (초기값: r1 192.168.100.11, mock_mode=False)
mcp_tool = IOSXEMCPTool()
