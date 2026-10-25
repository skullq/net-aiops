import json
import logging
import subprocess
import shutil
import time
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


class IOSXEMCPTool:
    """Cisco IOS-XE 100% 라이브 실측 MCP 도구 집합:

    1. 실제 장비(r1~r5: 192.168.100.11~15) 라이브 SSH 접속 및 실측 CLI 실행
    2. ntc-templates 기반 Show 명령어 결과 JSON 자동 파싱
    3. hier-config 기반 멱등적 교정(Remediation) CLI 생성
    4. 가상 Mock 모드를 완전히 배제하고 100% 실측 텔레메트리만 보장
    """

    def __init__(self, device_config: Optional[DeviceConfig] = None):
        self.config = device_config or DeviceConfig(
            host="192.168.100.11",
            port=22,
            username="admin",
            password="admin",
            enable_password="admin"
        )

    def update_config(self, device_config: DeviceConfig) -> None:
        self.config = device_config
        logger.info(f"IOSXEMCPTool updated target to live device: {device_config.host}:{device_config.port}")

    def execute_show_command(self, command: str, use_textfsm: bool = True) -> Dict[str, Any]:
        """Cisco IOS-XE 실제 장비에 Show 명령어를 수행하고 실측 raw 결과와 파싱된 JSON 데이터를 반환합니다."""
        clean_cmd = command.strip()
        logger.info(f"Executing live SSH command '{clean_cmd}' on real device {self.config.host}:{self.config.port} (user: {self.config.username})")
        return self._execute_live_ssh(clean_cmd, use_textfsm=use_textfsm)

    def _execute_live_ssh(self, command: str, use_textfsm: bool = True) -> Dict[str, Any]:
        """실제 Cisco IOS-XE 장비에 SSH로 접속하여 실시간 명령어를 실행합니다."""
        raw_output = ""
        success = False
        error_msg = None

        # Direct SSH Transport (sshpass / ssh CLI - 세션 점유 없이 단일 커맨드 즉시 실행 및 반납)
        ssh_pass = self.config.password or "admin"
        ssh_user = self.config.username or "admin"
        ssh_host = self.config.host
        ssh_port = str(self.config.port or 22)
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
        full_cmd = ["sshpass", "-p", ssh_pass] + ssh_cmd if has_sshpass else ssh_cmd

        # VTY 경합 회피를 위한 최대 2회 시도
        for attempt in range(1, 3):
            try:
                proc = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if proc.returncode == 0 and proc.stdout:
                    raw_output = proc.stdout
                    success = True
                    break
                else:
                    err_out = proc.stderr or proc.stdout or "Non-zero exit code"
                    logger.warning(f"Direct SSH attempt {attempt} failed on {ssh_host}: {err_out.strip()}")
                    error_msg = err_out
                    if attempt < 2:
                        time.sleep(0.5)
            except Exception as ssh_err:
                logger.error(f"Direct SSH error to {self.config.host} (attempt {attempt}): {ssh_err}")
                error_msg = str(ssh_err)
                if attempt < 2:
                    time.sleep(0.5)

        # 결과 파싱 및 반환
        if success and raw_output:
            parsed_output = None
            if use_textfsm:
                parsed_output = self._parse_with_ntc(command, raw_output)

            return {
                "success": True,
                "command": command,
                "host": self.config.host,
                "transport": "live-ssh",
                "raw_output": raw_output,
                "parsed_output": parsed_output,
                "error": None
            }

        # 실제 연결 실패 시: 가상 목업 데이터 생성 없이 엄격히 실패 반환
        logger.error(f"Live SSH connection to {self.config.host} failed: {error_msg}")
        return {
            "success": False,
            "command": command,
            "host": self.config.host,
            "transport": "live-ssh",
            "raw_output": f"% Error: 실제 장치({self.config.host})에 연결할 수 없습니다. (원인: {error_msg})\n% 모든 진단은 실측 라이브 연결을 통해서만 수행됩니다.",
            "parsed_output": None,
            "error": error_msg
        }

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


# 기본 싱글톤 인스턴스 (초기값: r1 192.168.100.11 실측 라이브)
mcp_tool = IOSXEMCPTool()
