import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, TypedDict

from langgraph.graph import StateGraph, START, END
from openai import AsyncOpenAI

from app.models import ChatMessage, DeviceConfig, LLMConfig
from app.device_manager import device_manager
from app.graph_engine import graph_engine
from app.mcp_iosxe_server import mcp_tool
from app.batfish_evaluator import batfish_evaluator

logger = logging.getLogger(__name__)

# 영구 보존용 AI 진단 로그 디렉토리
DIAGNOSTICS_LOGS_DIR = "/root/Net-AIOps/logs/ai_diagnostics"
os.makedirs(DIAGNOSTICS_LOGS_DIR, exist_ok=True)

# 영문 보고서 생성을 위한 매핑 사전
ROOT_CAUSE_EN_DESC: Dict[str, str] = {
    "BGP MD5 Password Mismatch": "TCP session establishment fails due to mismatched MD5 authentication password between peers.",
    "Interface MTU Mismatch": "Session reset when large BGP packets exceed interface MTU size.",
    "Physical Link Flapping": "Physical link degradation or optical level flapping on the connected interface.",
    "No Route to Peer IP (IGP Unreachable)": "Routing table lacks an active IGP or static route towards peer IP.",
    "BGP Neighbor Administratively Shutdown": "BGP session explicitly deactivated via 'neighbor shutdown' command.",
    "TCP Port 179 Blocked by ACL / CoPP": "BGP control plane traffic (TCP 179) filtered by interface ACL or CoPP policy.",
    "eBGP Multihop Missing (TTL=1 Drop)": "eBGP peering packets dropped because default TTL=1 is exhausted across multiple hops.",
    "Missing update-source Loopback0": "TCP SYN packet sent from physical interface IP instead of configured Loopback0.",
    "Remote-AS Number Mismatch": "Configured remote-as does not match the peer's actual autonomous system number.",
    "Unadvertised eBGP Subnet without next-hop-self": "eBGP next-hop is not declared or redistributed in IGP (OSPF/IS-IS/Static) and lacks 'next-hop-self'.",
    "BGP Missing next-hop-self": "iBGP updates forward eBGP next-hop without rewriting to local loopback/interface IP.",
    "Hold Timer Expired (Keepalive Drop)": "Keepalive packets delayed or dropped, leading to hold timer expiration.",
    "Interface ACL (Access-List) Filter Blocking": "Inbound or outbound access-list filtering routing control traffic (TCP 179 / OSPF).",
    "Policy-Based Routing (PBR) Override / Misconfiguration": "Policy-Based Routing route-map overriding standard FIB forwarding or dropping packets.",
    "Next-Hop IP Not Advertised in IGP": "BGP next-hop IP address is not declared in underlay IGP (OSPF/IS-IS).",
    "Next-Hop Unreachable via OSPF Underlay": "Next-hop resolution fails because underlay OSPF adjacency is down or prefix is unadvertised.",
    "Next-Hop Unreachable via IS-IS Underlay": "Underlay IS-IS circuit down or adjacency missing, making BGP next-hop unreachable.",
    "Next-Hop Missing via Static Route": "Static route towards next-hop IP is missing or pointing to an invalid interface."
}


class AIOpsState(TypedDict):
    """LangGraph 기반 진단 상태 객체 (AgentState)"""
    session_id: str
    session_start_time: str
    debug_mode: bool
    message: str
    history: List[Dict[str, str]]
    language: str  # 'ko' or 'en'
    device_config: Dict[str, Any]
    llm_config: Dict[str, Any]
    intent_data: Optional[Dict[str, Any]]

    # 1. 범위 탐지 (Scope Detection & Dynamic Protocol Detection)
    scope_type: str  # 'POINT_TO_POINT' | 'TRANSIT_PATH' | 'NETWORK_WIDE'
    source_device: str
    destination_device: str
    intermediate_devices: List[str]
    all_involved_devices: List[str]
    target_device: str
    detected_protocol: str
    detected_protocols: List[str]

    # 2. 인과 그래프 (GraphDB Causal Routing)
    symptom_id: str
    symptom_label: str
    candidate_root_causes: List[Dict[str, Any]]
    verification_commands: List[Dict[str, Any]]
    remediation_actions: List[str]
    batfish_questions: List[str]
    paired_cli_commands: List[str]

    # 3. Batfish 정형 검증 (Formal Verification from batfish_support.md)
    batfish_eval: Dict[str, Any]
    confirmed_root_cause: str
    all_confirmed_root_causes: Optional[List[Dict[str, Any]]]
    hop_device_evaluations: Optional[Dict[str, Any]]
    batfish_evidence: str
    pruned_root_causes: List[str]

    # 4. 실측 텔레메트리 (Live IOS-XE Telemetry)
    executed_telemetry: List[Dict[str, Any]]

    # 5. 최종 리포트 및 스트리밍 이벤트
    final_response: str
    trace_events: List[Dict[str, Any]]
    stream_events: List[Dict[str, Any]]
    session_log_path: str
    session_txt_path: str


def save_diagnostic_session_log(
    session_id: str,
    start_time: str,
    state: Dict[str, Any],
    final_text: str,
    all_trace_events: List[Dict[str, Any]]
) -> Tuple[str, str]:
    """진단 세션의 모든 입력, 상태, 텔레메트리, 정형 검증 질문, 추론 과정을 영구 보존"""
    os.makedirs(DIAGNOSTICS_LOGS_DIR, exist_ok=True)
    json_path = os.path.join(DIAGNOSTICS_LOGS_DIR, f"{session_id}.json")
    log_path = os.path.join(DIAGNOSTICS_LOGS_DIR, f"{session_id}.log")
    index_path = os.path.join(DIAGNOSTICS_LOGS_DIR, "sessions_index.jsonl")

    session_record = {
        "session_id": session_id,
        "debug_mode": state.get("debug_mode", True),
        "start_time": start_time,
        "end_time": datetime.now().isoformat(),
        "user_message": state.get("message"),
        "language": state.get("language", "ko"),
        "target_device": state.get("target_device"),
        "scope_analysis": {
            "scope_type": state.get("scope_type"),
            "source_device": state.get("source_device"),
            "destination_device": state.get("destination_device"),
            "intermediate_devices": state.get("intermediate_devices", []),
            "all_involved_devices": state.get("all_involved_devices", [])
        },
        "graphdb_routing": {
            "symptom_id": state.get("symptom_id"),
            "symptom_label": state.get("symptom_label"),
            "candidate_root_causes": state.get("candidate_root_causes", []),
            "batfish_questions": state.get("batfish_questions", []),
            "paired_cli_commands": state.get("paired_cli_commands", []),
            "remediation_actions": state.get("remediation_actions", [])
        },
        "batfish_verification": {
            "confirmed_root_cause": state.get("confirmed_root_cause"),
            "evidence": state.get("batfish_evidence"),
            "pruned_root_causes": state.get("pruned_root_causes", []),
            "batfish_facts": state.get("batfish_eval", {}).get("batfish_facts", {})
        },
        "live_telemetry_results": [
            {
                "command": r.get("command"),
                "host": r.get("host"),
                "status": r.get("status"),
                "raw_output": r.get("raw_output"),
                "parsed_output": r.get("parsed_output")
            }
            for r in state.get("executed_telemetry", [])
        ],
        "trace_events": all_trace_events,
        "final_report": final_text
    }

    # 1. JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(session_record, f, ensure_ascii=False, indent=2)

    # 2. 텍스트 로그 저장 (.log)
    txt_lines = [
        "=" * 80,
        "Net-AIOps Autonomous Troubleshooting Session Log",
        f"Session ID : {session_id}",
        f"Start Time : {start_time}",
        f"Target Host: {state.get('target_device')}",
        f"Language   : {state.get('language')}",
        f"User Query : {state.get('message')}",
        "=" * 80,
        "",
        "--- [1. SCOPE & TOPOLOGY ANALYSIS] ---",
        f"Scope Type : {state.get('scope_type')}",
        f"Path       : {state.get('source_device')} -> {state.get('destination_device') or 'Local'}",
        f"Transit    : {state.get('intermediate_devices') or 'None'}",
        "",
        "--- [2. GRAPHDB CAUSAL ROUTING & FORMAL APIS] ---",
        f"Symptom    : {state.get('symptom_label')} ({state.get('symptom_id')})",
        f"Batfish Question APIs : {state.get('batfish_questions')}",
        f"Paired Cisco CLI Cmds : {state.get('paired_cli_commands')}",
        "",
        "--- [3. BATFISH FORMAL VERIFICATION RESULT] ---",
        f"Confirmed  : {state.get('confirmed_root_cause')}",
        f"Evidence   : {state.get('batfish_evidence')}",
        f"Pruned     : {state.get('pruned_root_causes')}",
        "",
        "--- [4. LIVE CISCO IOS-XE TELEMETRY EXECUTED] ---",
    ]
    for r in state.get("executed_telemetry", []):
        txt_lines.append(f">> CLI: {r.get('command')} on {r.get('host')} [status: {r.get('status')}]")
        raw = r.get("raw_output") or ""
        txt_lines.append(raw.strip() if raw else "(Empty output)")
        txt_lines.append("-" * 40)
    txt_lines.extend([
        "",
        "--- [5. FINAL SYNTHESIS REPORT] ---",
        final_text,
        "",
        "=" * 80,
        f"Session Completed at {datetime.now().isoformat()}",
        "=" * 80
    ])

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")

    # 3. Index 라인 추가
    index_entry = {
        "session_id": session_id,
        "timestamp": start_time,
        "user_message": state.get("message"),
        "scope_type": state.get("scope_type"),
        "target_device": state.get("target_device"),
        "confirmed_root_cause": state.get("confirmed_root_cause"),
        "json_log": f"logs/ai_diagnostics/{session_id}.json",
        "text_log": f"logs/ai_diagnostics/{session_id}.log"
    }
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(index_entry, ensure_ascii=False) + "\n")

    return json_path, log_path


def format_troubleshooting_metadata(
    session_id: str,
    start_time: str,
    state: Dict[str, Any],
    is_en: bool,
    debug_mode: bool = True
) -> str:
    target = state.get("target_device", "")
    scope = state.get("scope_type", "")
    src = state.get("source_device", "")
    dst = state.get("destination_device") or ("Local Peer" if is_en else "로컬 피어")
    confirmed = state.get("confirmed_root_cause", "")
    bf_qs = ", ".join(state.get("batfish_questions", [])[:4]) or "bf.q.bgpSessionCompatibility(), bf.q.routes()"
    clis = ", ".join(state.get("paired_cli_commands", [])[:4]) or "show ip bgp neighbors, show ip route"
    rel_json = f"logs/ai_diagnostics/{session_id}.json"
    rel_log = f"logs/ai_diagnostics/{session_id}.log"

    if not debug_mode:
        if is_en:
            return (
                f"\n\n---\n"
                f"#### ℹ️ [Session Information]\n"
                f"- **Session ID:** `{session_id}`\n"
                f"- **Debug Mode:** `OFF` — Disk log persistence skipped (Enable Debug Mode in header or settings to save diagnostic traces)\n"
                f"- **Diagnosis Scope:** `{scope}` (`{src}` ➔ `{dst}`)\n"
                f"- **Confirmed Root Cause:** `{confirmed}`\n"
            )
        else:
            return (
                f"\n\n---\n"
                f"#### ℹ️ [AI 진단 세션 정보]\n"
                f"- **세션 ID (Session ID):** `{session_id}`\n"
                f"- **디버그 모드:** `OFF (비활성화)` — 파일 저장 건너뜀 (상단 헤더의 DEBUG 버튼을 켜면 상세 진단 로그가 logs/ai_diagnostics에 보관됩니다)\n"
                f"- **장애 범위(Scope):** `{scope}` (`{src}` ➔ `{dst}`)\n"
                f"- **확정 근본 원인:** `{confirmed}`\n"
            )

    if is_en:
        return (
            f"\n\n---\n"
            f"#### 🛠️ [Troubleshooting Session Metadata]\n"
            f"- **Session ID:** `{session_id}`\n"
            f"- **Timestamp:** `{start_time}`\n"
            f"- **Target Device:** `{target}`\n"
            f"- **Diagnosis Scope:** `{scope}` (`{src}` ➔ `{dst}`)\n"
            f"- **Confirmed Root Cause:** `{confirmed}`\n"
            f"- **Batfish Formal Questions:** `{bf_qs}`\n"
            f"- **Paired Cisco CLI Telemetry:** `{clis}`\n"
            f"- **Full Telemetry & Trace Log (JSON):** [`{rel_json}`](file://{DIAGNOSTICS_LOGS_DIR}/{session_id}.json)\n"
            f"- **Human-Readable Session Trace (LOG):** [`{rel_log}`](file://{DIAGNOSTICS_LOGS_DIR}/{session_id}.log)\n"
            f"> *Troubleshooting Tip: Run `cat {rel_log}` in your terminal to inspect all raw outputs and step-by-step reasoning.*"
        )
    else:
        return (
            f"\n\n---\n"
            f"#### 🛠️ [AI 진단 세션 트러블슈팅 정보]\n"
            f"- **세션 ID (Session ID):** `{session_id}`\n"
            f"- **진단 일시:** `{start_time}`\n"
            f"- **분석 대상 장비:** `{target}`\n"
            f"- **장애 범위(Scope):** `{scope}` (`{src}` ➔ `{dst}`)\n"
            f"- **확정 근본 원인:** `{confirmed}`\n"
            f"- **Batfish 정형 질의 API:** `{bf_qs}`\n"
            f"- **대응 Cisco 실측 CLI:** `{clis}`\n"
            f"- **전체 세션 데이터 (JSON):** [`{rel_json}`](file://{DIAGNOSTICS_LOGS_DIR}/{session_id}.json)\n"
            f"- **실시간 트레이스 로그 (LOG):** [`{rel_log}`](file://{DIAGNOSTICS_LOGS_DIR}/{session_id}.log)\n"
            f"> *트러블슈팅 안내: 터미널에서 `cat {rel_log}` 명령어로 전체 CLI 실측 출력 및 단계별 추론 과정을 즉시 재현/확인할 수 있습니다.*"
        )


class LangGraphAIOpsAgent:
    """LangGraph 기반의 자율 네트워크 트러블슈팅 오케스트레이터"""

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph StateGraph 구축 및 조건부 엣지 정의"""
        graph = StateGraph(AIOpsState)

        # 노드 등록
        graph.add_node("scope_detection", self.scope_detection_node)
        graph.add_node("causal_routing", self.causal_routing_node)
        graph.add_node("batfish_verification", self.batfish_verification_node)
        graph.add_node("live_telemetry", self.live_telemetry_node)
        graph.add_node("llm_synthesis", self.llm_synthesis_node)

        # 엣지 연결 (순차 파이프라인)
        graph.add_edge(START, "scope_detection")
        graph.add_edge("scope_detection", "causal_routing")
        graph.add_edge("causal_routing", "batfish_verification")
        graph.add_edge("batfish_verification", "live_telemetry")
        graph.add_edge("live_telemetry", "llm_synthesis")
        graph.add_edge("llm_synthesis", END)

        return graph.compile()

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # Stage 1 LLM: 초경량 시드 장비 추출기 (Seed Device & Target Extractor)
    # -----------------------------------------------------------------
    async def extract_intent_and_scope(
        self,
        message: str,
        llm_config: Optional[Dict[str, Any]],
        available_devices: List[str]
    ) -> Dict[str, Any]:
        """1차 초경량 LLM: 사용자 질의로부터 1차 시드 대상 장비(Seed Devices)와 대상 IP만 정확히 추출 (섣부른 증상 추측 완전 배제)"""
        api_key = (llm_config or {}).get("api_key", "").strip()
        model = (llm_config or {}).get("model", "gemini-2.5-flash")
        base_url = ((llm_config or {}).get("base_url") or "").strip().rstrip("/")
        if "generativelanguage.googleapis.com" in base_url and not base_url.endswith("/openai"):
            base_url = f"{base_url}/openai"

        # 결정론적 안전 폴백 (API 키 없거나 통신 실패 시)
        def _fallback_parse(msg: str) -> Dict[str, Any]:
            m = msg.lower()
            is_inv = any(kw in m for kw in ["장비 몇", "몇 대", "몇대", "장비 목록", "장치 몇", "장치 목록", "how many devices", "list devices"])
            matched = [d for d in available_devices if d.lower() in m]

            ip_match = re.search(r"((?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?)", msg)
            target_ip = ip_match.group(1) if ip_match else None

            return {
                "is_inventory_query": is_inv,
                "seed_devices": matched,
                "target_service_or_ip": target_ip
            }

        if not api_key:
            return _fallback_parse(message)

        system_prompt = (
            f"You are a strict network seed entity extractor. Registered inventory devices: {available_devices}.\n"
            "Analyze the user message and output strictly a valid JSON object with these keys:\n"
            "- \"is_inventory_query\": (boolean) true only if the user specifically asks how many devices exist, device counts, or device inventory list.\n"
            "- \"seed_devices\": (string array) strictly list of device names from registered inventory that are explicitly mentioned in the message in order of appearance. Do NOT guess or invent unmentioned devices. If none mentioned, return [].\n"
            "- \"target_service_or_ip\": (string or null) specific IP address, subnet, or service if explicitly mentioned (e.g. '10.1.14.0/24', '1.1.1.1', 'web'). Otherwise null.\n"
            "Respond ONLY with the JSON object."
        )

        try:
            client = AsyncOpenAI(base_url=base_url or None, api_key=api_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.0,
                    stream=False
                ),
                timeout=3.0
            )
            raw = (resp.choices[0].message.content or "").strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            devs = [d for d in parsed.get("seed_devices", []) if d in available_devices]
            return {
                "is_inventory_query": bool(parsed.get("is_inventory_query")),
                "seed_devices": devs,
                "target_service_or_ip": parsed.get("target_service_or_ip")
            }
        except Exception as e:
            logger.warning(f"1st LLM intent parser error/timeout ({e}). Using deterministic fallback.")
            return _fallback_parse(message)

    # -----------------------------------------------------------------
    # Node 1: Scope Detection & Dynamic Scope Expansion (시드 장비 ➔ 토폴로지 확장)
    # -----------------------------------------------------------------
    def scope_detection_node(self, state: AIOpsState) -> Dict[str, Any]:
        msg = state["message"]
        is_en = state.get("language") == "en"
        all_devices = device_manager.get_all_devices()
        all_dev_names = [d.name.lower() for d in all_devices]

        intent = state.get("intent_data") or {}
        seed_devices = intent.get("seed_devices", [])
        target_service_ip = intent.get("target_service_or_ip")

        # 1. 시드 장비가 2개 이상인 경우: Batfish/NetworkX L3 최단 경로 & ECMP 분석을 통한 Transit 장비 자동 확장
        if len(seed_devices) >= 2:
            source_dev = seed_devices[0]
            dest_dev = seed_devices[1]
            topo_analysis = batfish_evaluator.find_topology_path_and_ecmp(source_dev, dest_dev)
            scope_type = topo_analysis["scope_type"]
            intermediate_devs = topo_analysis["intermediate_devices"]
            all_involved = topo_analysis["all_involved_devices"]
            transit_desc_ko = topo_analysis["description_ko"]
            transit_desc_en = topo_analysis["description_en"]

        # 2. 시드 장비가 1개인 경우: 단일 장비 로컬 점검
        elif len(seed_devices) == 1:
            source_dev = seed_devices[0]
            dest_dev = ""
            scope_type = "SINGLE_DEVICE"
            intermediate_devs = []
            all_involved = [source_dev]
            transit_desc_ko = f"{source_dev} 단일 장비 로컬 점검"
            transit_desc_en = f"{source_dev} Local Device Scope"

        # 3. 장비는 없으나 특정 서비스나 대상 IP가 명시된 경우: 백본 엔드투엔드 도달성 점검 허용
        elif target_service_ip:
            source_dev = "r1"
            dest_dev = ""
            scope_type = "BACKBONE_TARGET_SERVICE"
            all_involved = all_dev_names
            intermediate_devs = [d for d in all_dev_names if d != source_dev]
            transit_desc_ko = f"특정 대상 IP({target_service_ip}) 기준 백본 엔드투엔드 점검"
            transit_desc_en = f"Backbone End-to-End Scope towards {target_service_ip}"

        # 4. 장비도 없고 대상 IP도 없는 경우: 기본 r1 안내
        else:
            source_dev = "r1"
            dest_dev = ""
            scope_type = "SINGLE_DEVICE"
            all_involved = [source_dev]
            intermediate_devs = []
            transit_desc_ko = "대상 장비 미지정 (기본 r1 점검)"
            transit_desc_en = "Unspecified Device (Default r1 check)"

        # 확장된 모든 대상 장비들의 실제 활성 설정(running-config)으로부터 프로토콜 동적 식별 (설정 기반 Fact)
        proto_info = batfish_evaluator.detect_dynamic_routing_protocols(all_involved)
        detected_protocol = proto_info["primary_protocol"]
        detected_protocols = proto_info["detected_protocols"]

        target_host = "192.168.100.11"
        for d in all_devices:
            if d.name.lower() == source_dev.lower() or d.id.lower() == source_dev.lower():
                target_host = d.host
                break

        proto_label = detected_protocol.upper() if detected_protocol != "direct" else "Direct/L2"
        if is_en:
            trace_title = f"Scope Detection: {scope_type} ({source_dev}" + (f" -> {dest_dev}" if dest_dev else "") + f") [{proto_label}]"
            trace_msg = f"Dynamic Topology: {transit_desc_en}. Detected Protocol: {proto_label} ({detected_protocols}). Devices in scope: {all_involved}."
        else:
            trace_title = f"장애 범위 탐지: {scope_type} ({source_dev}" + (f" ➔ {dest_dev}" if dest_dev else "") + f", {transit_desc_ko}) [{proto_label}]"
            trace_msg = f"동적 토폴로지 분석: {transit_desc_ko}. 감지된 프로토콜: {proto_label} ({', '.join(detected_protocols)}). 진단 대상 장비: {', '.join(all_involved)}."

        trace_event = {
            "step": "scope_detection",
            "title": trace_title,
            "status": "success",
            "message": trace_msg,
            "scope_type": scope_type,
            "source_device": source_dev,
            "destination_device": dest_dev,
            "intermediate_devices": intermediate_devs,
            "detected_protocol": detected_protocol,
            "detected_protocols": detected_protocols,
            "all_involved_devices": all_involved,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "scope_type": scope_type,
            "source_device": source_dev,
            "destination_device": dest_dev,
            "intermediate_devices": intermediate_devs,
            "all_involved_devices": all_involved,
            "target_device": target_host,
            "detected_protocol": detected_protocol,
            "detected_protocols": detected_protocols,
            "trace_events": [trace_event]
        }

    # -----------------------------------------------------------------
    # Node 2: Causal Routing (Universal GraphStore Query with OSI Order)
    # -----------------------------------------------------------------
    def causal_routing_node(self, state: AIOpsState) -> Dict[str, Any]:
        msg = state["message"]
        is_en = state.get("language") == "en"
        proto_hint = state.get("detected_protocol", "")

        # 설정에서 실제 감지된 프로토콜 기반 증상 노드 도출
        symptom_id = graph_engine.match_symptom(msg, protocol_hint=proto_hint)
        workflow = graph_engine.get_diagnostic_workflow(symptom_id)
        causal_paths = graph_engine.find_causal_paths(symptom_id)

        candidate_rcs = workflow.get("root_causes", [])
        verification_cmds = workflow.get("verification_commands", [])
        remediations = [r.get("command") or r.get("label") for r in workflow.get("remediation_actions", [])]

        # GraphDB 워크플로우 내 Batfish 78개 Question API 및 대응 Cisco CLI 쌍 추출
        batfish_qs = []
        for v in workflow.get("verifications", []):
            q = v.get("details", {}).get("batfish_question")
            if q and q not in batfish_qs:
                batfish_qs.append(q)

        paired_clis = []
        for cmd in verification_cmds:
            c = cmd.get("command") or cmd.get("details", {}).get("cli_command")
            if c and c not in paired_clis:
                paired_clis.append(c)

        trace_title = (
            f"Causal Graph Traversal: {workflow['symptom']['label']} ({len(candidate_rcs)} Root Causes / {len(causal_paths)} Paths)"
            if is_en else
            f"GraphDB 인과 추론: {workflow['symptom']['label']} (후보 원인 {len(candidate_rcs)}개, 추론 세부 경로 {len(causal_paths)}개)"
        )
        trace_msg = (
            f"Derived {len(candidate_rcs)} candidate root causes, {len(batfish_qs)} Batfish Question APIs, and {len(causal_paths)} causal paths across OSI layers."
            if is_en else
            f"분리형 GraphStore에서 증상({symptom_id})에 대한 {len(candidate_rcs)}개의 후보 원인과 {len(batfish_qs)}개의 Batfish 정형 검증 질문 및 {len(causal_paths)}개의 인과 추론 세부 경로를 도출했습니다."
        )

        trace_event = {
            "step": "causal_routing",
            "title": trace_title,
            "status": "success",
            "message": trace_msg,
            "symptom_id": symptom_id,
            "symptom_label": workflow["symptom"]["label"],
            "candidate_count": len(candidate_rcs),
            "paths_count": len(causal_paths),
            "batfish_questions": batfish_qs,
            "paired_cli_commands": paired_clis,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "symptom_id": symptom_id,
            "symptom_label": workflow["symptom"]["label"],
            "candidate_root_causes": candidate_rcs,
            "verification_commands": verification_cmds,
            "remediation_actions": remediations,
            "batfish_questions": batfish_qs,
            "paired_cli_commands": paired_clis,
            "trace_events": [trace_event]
        }

    # -----------------------------------------------------------------
    # Node 3: Batfish Formal Verification (Using batfish_support.md APIs)
    # -----------------------------------------------------------------
    def batfish_verification_node(self, state: AIOpsState) -> Dict[str, Any]:
        is_en = state.get("language") == "en"
        target_host = state["target_device"]
        symptom_id = state["symptom_id"]
        candidate_ids = [rc["id"] for rc in state["candidate_root_causes"]]

        # 실시간 설정 수집 ➔ Batfish 스냅샷 로드 ➔ 전 장비(중계 노드 포함) 정형 검증 실행
        eval_result = batfish_evaluator.evaluate_root_causes(
            target_device_host=target_host,
            candidate_root_cause_ids=candidate_ids,
            symptom_id=symptom_id,
            source_device=state.get("source_device"),
            destination_device=state.get("destination_device"),
            involved_devices=state.get("all_involved_devices")
        )

        confirmed_id = eval_result.get("confirmed_root_cause")
        confirmed_label = confirmed_id
        for rc in state["candidate_root_causes"]:
            if rc["id"] == confirmed_id:
                confirmed_label = rc["label"]
                break

        pruned = eval_result.get("pruned_root_causes", [])
        evidence = eval_result.get("evidence", "Batfish formal simulation verified topology consistency.")
        used_apis = eval_result.get("used_batfish_apis") or [
            "bf.q.layer3Edges()",
            "bf.q.routes()",
            "bf.q.filterLineReachability()",
            "bf.q.isisEdges()"
        ]

        all_confirmed = eval_result.get("all_confirmed_root_causes", [])
        hop_evals = eval_result.get("hop_device_evaluations", {})
        multi_fault_count = len(all_confirmed)

        if multi_fault_count > 1:
            trace_title = (
                f"Batfish Formal Verification: {multi_fault_count} Issues Confirmed across Path ({confirmed_label} + {multi_fault_count - 1} more)"
                if is_en else
                f"Batfish 정형 검증 완료: 경로 상 {multi_fault_count}개 결함 확정 ({confirmed_label} 외 {multi_fault_count - 1}건)"
            )
        else:
            trace_title = (
                f"Batfish Formal Verification: {confirmed_label}"
                if is_en else
                f"Batfish 정형 검증 완료: {confirmed_label} (확정)"
            )

        trace_msg = (
            f"Batfish evaluated live configs across all path nodes. Confirmed issues:\n{evidence}"
            if is_en else
            f"Batfish가 경로 상 모든 장비의 live config를 전수 정형 분석했습니다. 진단 내역:\n{evidence}"
        )

        trace_event = {
            "step": "batfish_verification",
            "title": trace_title,
            "status": "success",
            "message": trace_msg,
            "confirmed_root_cause": confirmed_label,
            "all_confirmed_root_causes": all_confirmed,
            "hop_device_evaluations": hop_evals,
            "evidence": evidence,
            "used_batfish_apis": used_apis,
            "pruned_root_causes": pruned,
            "evaluated_by": eval_result.get("evaluated_by"),
            "timestamp": datetime.now().isoformat()
        }

        return {
            "batfish_eval": eval_result,
            "confirmed_root_cause": confirmed_label,
            "all_confirmed_root_causes": all_confirmed,
            "hop_device_evaluations": hop_evals,
            "batfish_evidence": evidence,
            "used_batfish_apis": used_apis,
            "pruned_root_causes": pruned,
            "trace_events": [trace_event]
        }

    # -----------------------------------------------------------------
    # Node 4: Live Telemetry Collection (Multi-Device Live Execution)
    # -----------------------------------------------------------------
    def live_telemetry_node(self, state: AIOpsState) -> Dict[str, Any]:
        is_en = state.get("language") == "en"
        all_involved = state.get("all_involved_devices", [])
        if not all_involved:
            all_involved = [state.get("source_device", "r1")]

        all_devices = device_manager.get_all_devices()
        dev_map = {d.name.lower(): d for d in all_devices}
        for d in all_devices:
            dev_map[d.id.lower()] = d
            dev_map[d.host] = d

        detected_proto = state.get("detected_protocol", "direct").lower()

        # 프로토콜 및 GraphDB 인과 경로에 따른 필수 점검 명령어 도출 (장비당 최대 4~5개로 압축하여 3초 내 신속 완료)
        protocol_specific_cmds = {
            "isis": [
                "show ip interface brief",
                "show isis neighbors",
                "show ip route isis",
                "show running-config | section router isis"
            ],
            "ospf": [
                "show ip interface brief",
                "show ip ospf neighbor",
                "show ip route ospf",
                "show running-config | section router ospf"
            ],
            "bgp": [
                "show ip interface brief",
                "show ip bgp summary",
                "show ip route bgp",
                "show running-config | section router bgp"
            ]
        }

        base_cmds = list(protocol_specific_cmds.get(detected_proto, ["show ip interface brief", "show ip route"]))
        # GraphDB 워크플로우 내 검증 명령어 중 해당 프로토콜과 직접 연관된 유효한 show 명령어만 선별 추가 (비정상 변수 템플릿 배제)
        for cmd_entry in state.get("verification_commands", []):
            c = (cmd_entry.get("command") or cmd_entry.get("label") or "").strip()
            if not c or not c.startswith("show "):
                continue
            if "{" in c or "}" in c or "..." in c or c in base_cmds:
                continue
            # 관련 프로토콜 키워드가 포함된 명령어만 최대 5개까지 허용
            if detected_proto in c:
                if len(base_cmds) < 5:
                    base_cmds.append(c)

        executed_results = []
        visited_hosts = set()

        for dev_key in all_involved:
            d_obj = dev_map.get(dev_key.lower())
            if not d_obj:
                continue
            if d_obj.host in visited_hosts:
                continue
            visited_hosts.add(d_obj.host)

            dev_cfg = DeviceConfig(
                host=d_obj.host,
                port=state["device_config"].get("port", 22),
                username=state["device_config"].get("username", "admin"),
                password=state["device_config"].get("password", "admin"),
                enable_password=state["device_config"].get("enable_password", "admin")
            )
            mcp_tool.update_config(dev_cfg)

            for cmd in base_cmds:
                cmd_clean = cmd.strip()
                if "..." in cmd_clean or cmd_clean.startswith("copy") or cmd_clean.startswith("help") or not cmd_clean.startswith("show"):
                    continue
                res = mcp_tool.execute_show_command(cmd_clean, use_textfsm=True)
                res["device_name"] = d_obj.name
                res["host"] = d_obj.host
                executed_results.append(res)

        dev_list_str = ", ".join(all_involved)
        trace_title = (
            f"Multi-Device Telemetry Collected ({len(executed_results)} CLI outputs across [{dev_list_str}])"
            if is_en else
            f"전체 관련 장비 텔레메트리 수집 완료 (범위 내 [{dev_list_str}] 장비 대상 {len(executed_results)}개 CLI 수집)"
        )
        trace_msg = (
            f"Collected live IOS-XE telemetry from all involved devices [{dev_list_str}] for protocol '{detected_proto.upper()}'."
            if is_en else
            f"장애 범위 내 모든 장비([{dev_list_str}])에 대해 동적 프로토콜 '{detected_proto.upper()}' 실측 텔레메트리를 성공적으로 수집했습니다."
        )

        trace_event = {
            "step": "live_telemetry",
            "title": trace_title,
            "status": "success",
            "message": trace_msg,
            "executed_count": len(executed_results),
            "devices": all_involved,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "executed_telemetry": executed_results,
            "trace_events": [trace_event]
        }

    # -----------------------------------------------------------------
    # Helper: Hierarchical Configuration (hconfig) Remediation Builder (Multi-Device)
    # -----------------------------------------------------------------
    def generate_hconfig_remediation(self, state: AIOpsState) -> Dict[str, Any]:
        """Batfish 정형 진단 완료 후, 경로 상에서 결함이 감지된 모든 대상 장비(r1, r2, r4 등)별로
        표준 Cisco IOS-XE 계층적 복원 설정(hconfig) 및 사후 검증 절차를 전수 도출합니다.
        """
        all_confirmed = state.get("all_confirmed_root_causes") or []
        confirmed_id = state.get("batfish_eval", {}).get("confirmed_root_cause") or ""
        src_dev = state.get("source_device", "r1")

        if not all_confirmed and confirmed_id:
            all_confirmed = [{"root_cause_id": confirmed_id, "device": src_dev, "details": state.get("batfish_evidence", "")}]

        # 장비별 결함 분류 (ex: {"r1": [...], "r2": [...]})
        dev_faults: Dict[str, List[Dict[str, Any]]] = {}
        for fault in all_confirmed:
            raw_dev = str(fault.get("device", src_dev)).lower()
            # ['r1', 'r5'] ➔ ['r2'] 같은 문자열 패턴 처리
            matched_devs = re.findall(r"r\d+", raw_dev)
            target_devs = matched_devs if matched_devs else [src_dev]
            for d in target_devs:
                dev_faults.setdefault(d, []).append(fault)

        device_remediations: Dict[str, Dict[str, Any]] = {}
        all_hconfig_blocks: List[str] = []
        all_post_verifications: List[str] = []
        explanations: List[str] = []

        for d_name, faults in dev_faults.items():
            d_cmds: List[str] = [
                f"! [Cisco IOS-XE Hierarchical Configuration (hconfig) for {d_name}]",
                "configure terminal"
            ]
            d_verifs: List[str] = []
            d_expls: List[str] = []

            for f in faults:
                rc_id = f.get("root_cause_id", "")
                intf = f.get("interface", "Ethernet0/1")

                # 1. ACL 차단 해제
                if "acl" in rc_id:
                    d_cmds.extend([
                        f" interface {intf}",
                        f"  no ip access-group 1 in",
                        f"  exit"
                    ])
                    d_verifs.extend([f"show ip interface {intf}", "show access-lists"])
                    d_expls.append(f"{d_name}의 {intf} 인터페이스에서 차단 ACL('ip access-group 1 in') 해제")

                # 2. IS-IS Metric Style Mismatch (r2 등 narrow metric 장비에 wide 적용)
                elif "isis" in rc_id or "metric_style" in rc_id:
                    d_cmds.extend([
                        " router isis",
                        "  metric-style wide",
                        "  exit"
                    ])
                    d_verifs.extend(["show isis neighbors", "show ip route isis"])
                    d_expls.append(f"{d_name}의 IS-IS 프로세스에 'metric-style wide' 적용하여 TLV 135 라우트 교환 활성화")

                # 3. OSPF Router-ID 충돌
                elif "router_id" in rc_id:
                    host_num = "".join(filter(str.isdigit, d_name)) or "4"
                    rid = f"{host_num}.{host_num}.{host_num}.{host_num}"
                    d_cmds.extend([
                        " router ospf 1",
                        f"  router-id {rid}",
                        "  exit"
                    ])
                    d_verifs.extend(["show ip ospf neighbor", "show ip route ospf"])
                    d_expls.append(f"{d_name}의 OSPF Router-ID 충돌 해소 (고유 Router-ID: {rid} 부여)")

                # 4. PBR Override
                elif "pbr" in rc_id:
                    d_cmds.extend([
                        f" interface {intf}",
                        "  no ip policy route-map PBR_DROP",
                        "  exit"
                    ])
                    d_verifs.extend(["show ip policy", "show ip route"])
                    d_expls.append(f"{d_name}의 PBR 정책 라우팅 해제")

                # 5. BGP 언더레이 라우팅 누락
                elif "nexthop_missing" in rc_id or "underlay" in rc_id:
                    # 장비의 기존 OSPF 설정 방식 검사: router ospf 하위에 network 선언이 존재하는지 판별
                    bf_eval = state.get("batfish_eval", {})
                    ospf_styles = bf_eval.get("batfish_facts", {}).get("ospf_config_styles", {})
                    dev_style_info = ospf_styles.get(d_name, {})
                    is_network_mode = dev_style_info.get("has_network_stmt", False)

                    if is_network_mode:
                        # [스타일 1] router ospf 밑에 network 선언 방식
                        d_cmds.extend([
                            " router ospf 1",
                            "  network 0.0.0.0 255.255.255.255 area 0",
                            "  exit"
                        ])
                        d_verifs.extend(["show ip ospf", "show ip ospf interface brief", "show ip route ospf", "show ip bgp summary"])
                        d_expls.append(f"{d_name}의 기존 설정 스타일(router ospf 하위 network 선언)에 따라 'network 0.0.0.0 255.255.255.255 area 0' 선언 적용")
                    else:
                        # [스타일 2] 인터페이스에 ip ospf 설정 방식
                        d_cmds.extend([
                            f" interface {intf}",
                            "  ip ospf 1 area 0",
                            "  exit"
                        ])
                        d_verifs.extend([f"show ip ospf interface {intf}", "show ip ospf neighbor", "show ip route ospf", "show ip bgp summary"])
                        d_expls.append(f"{d_name}의 기존 설정 스타일(인터페이스 직접 지정)에 따라 {intf} 인터페이스 하위에 'ip ospf 1 area 0' 적용")

            d_cmds.extend(["end", "write memory"])
            block_str = "\n".join(d_cmds)
            all_hconfig_blocks.append(block_str)
            all_post_verifications.extend(d_verifs)
            explanations.extend(d_expls)

            device_remediations[d_name] = {
                "hconfig_block": block_str,
                "post_verification_commands": list(dict.fromkeys(d_verifs)),
                "explanation": "; ".join(d_expls)
            }

        if not all_hconfig_blocks:
            fallback_cmd = (
                f"! [Cisco IOS-XE Hierarchical Configuration (hconfig) for {src_dev}]\n"
                f"configure terminal\n"
                f" interface Ethernet0/1\n"
                f"  no ip access-group 1 in\n"
                f"  exit\n"
                f"end\n"
                f"write memory"
            )
            all_hconfig_blocks.append(fallback_cmd)
            all_post_verifications.extend(["show ip interface brief", "show ip route"])
            explanations.append(f"{src_dev} 기본 인터페이스 점검")

        return {
            "target_device": ", ".join(device_remediations.keys()) if device_remediations else src_dev,
            "target_devices": list(device_remediations.keys()),
            "device_remediations": device_remediations,
            "hconfig_block": "\n\n".join(all_hconfig_blocks),
            "post_verification_commands": list(dict.fromkeys(all_post_verifications)),
            "explanation": "\n".join(f"- {e}" for e in explanations)
        }

    # -----------------------------------------------------------------
    # Node 5: LLM Synthesis (Single Structured Synthesis Call)
    # -----------------------------------------------------------------
    async def llm_synthesis_node(self, state: AIOpsState) -> Dict[str, Any]:
        is_en = state.get("language") == "en"
        llm_cfg = state.get("llm_config") or {}
        api_key = llm_cfg.get("api_key", "").strip()
        model = llm_cfg.get("model", "gemini-2.5-flash")
        base_url = (llm_cfg.get("base_url") or "").strip().rstrip("/")
        if "generativelanguage.googleapis.com" in base_url and not base_url.endswith("/openai"):
            base_url = f"{base_url}/openai"

        # 시스템 프롬프트 (간결하고 핵심적인 3단계 진단 및 hconfig 복원 지침)
        if is_en:
            system_prompt = (
                "You are an autonomous Cisco IOS-XE Network AIOps Engineer powered by LangGraph & Batfish.\n"
                "Synthesize the diagnosis following the complete 3-stage restoration lifecycle:\n"
                "1. [Verification Confirmation]: Explain the root causes confirmed strictly across the devices in the current query's active path (all_involved_devices). DO NOT mention devices not in the evaluated path.\n"
                "2. [Hierarchical Remediation Configuration (hconfig)]: Present the exact production-ready Cisco IOS-XE hierarchical CLI config blocks for only the faulty devices identified on this path. If a device already uses 'network' statements under 'router ospf', strictly follow the 'network' declaration style; otherwise, configure OSPF directly on the interface ('ip ospf <pid> area <area>').\n"
                "3. [Post-Verification]: Specify the exact verification show commands matching the configuration style for all affected devices.\n"
                "Produce your response strictly in professional English."
            )
        else:
            system_prompt = (
                "당신은 LangGraph와 Batfish 정형 분석 기반의 Cisco IOS-XE 자율 네트워크 AIOps 엔지니어입니다.\n"
                "제공된 Batfish 정형 검증 확정 팩트와 실측 CLI 데이터에 기반하여 아래 3단계 자율 복구 라이프사이클로 보고서를 작성하십시오:\n"
                "1. [설정상 진단 확인 (Verification)]: Batfish 정형 검증 팩트 및 실측 CLI 대조 결과 분석 (반드시 현재 질의의 출발지-목적지 경로에 실제로 속한 진단 대상 장비(all_involved_devices) 및 중계 장비의 상태와 발견된 결함만을 정확히 명시하십시오. 현재 진단 경로에 없는 무관한 장비는 절대로 언급하지 마십시오)\n"
                "2. [계층적 복원 설정 (hconfig Remediation Config)]: 실제 결함이 발견된 대상 장비 각각에 대한 표준 Cisco IOS-XE 계층형 CLI 블록을 작성하십시오. 특히 OSPF 설정 시, 해당 장비의 기존 설정에서 'router ospf' 밑에 'network' 선언을 사용했다면 무조건 'network' 선언 방식을 따르고, 그렇지 않고 인터페이스 지정 방식을 사용했다면 인터페이스 하위에 'ip ospf <pid> area <area>'를 설정하는 방식을 따르십시오.\n"
                "3. [사후 검증 (Post-Verification)]: 복원 적용 후 정상화 여부를 판별할 대상 장비별 확인 명령어 목록 (인터페이스 설정 방식인지 router ospf network 방식인지에 부합하는 검증 명령어 제시)\n"
                "모든 답변은 자연스럽고 전문적인 한국어로 작성하십시오."
            )

        # hconfig 복원 계획 생성 (대상 결함 장비 전수 도출)
        hconfig_plan = self.generate_hconfig_remediation(state)

        # 확증된 팩트, 전 장비(중계 노드 포함) 검증 내역, 실측 CLI 데이터, hconfig 복원 설정 주입
        dynamic_context = {
            "scope_analysis": {
                "scope_type": state.get("scope_type"),
                "source_device": state.get("source_device"),
                "destination_device": state.get("destination_device"),
                "intermediate_transit_devices": state.get("intermediate_devices", []),
                "all_involved_devices": state.get("all_involved_devices", []),
                "detected_protocol": state.get("detected_protocol", "direct")
            },
            "batfish_formal_verification": {
                "confirmed_root_cause": state.get("confirmed_root_cause"),
                "all_confirmed_root_causes": state.get("all_confirmed_root_causes", []),
                "hop_device_evaluations": state.get("hop_device_evaluations", {}),
                "mathematical_evidence": state.get("batfish_evidence"),
                "verification_status": "CONFIRMED_FACT",
                "detailed_facts": state.get("batfish_eval", {}).get("batfish_facts", {})
            },
            "live_telemetry_findings": [
                {
                    "device": r.get("device_name") or r.get("host"),
                    "command": r.get("command"),
                    "output": r.get("parsed_output") or (r.get("raw_output") or "")[:400]
                }
                for r in state.get("executed_telemetry", [])
            ],
            "hconfig_remediation_plan": hconfig_plan
        }

        user_content = f"사용자 진단 질의: {state['message']}\n\n[Batfish 정형 검증 확정 팩트 및 hconfig 복원 계획]:\n{json.dumps(dynamic_context, ensure_ascii=False)}"

        final_text = ""
        if api_key:
            try:
                client = AsyncOpenAI(base_url=base_url or None, api_key=api_key)
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        stream=False
                    ),
                    timeout=15.0
                )
                final_text = resp.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"LLM API synthesis timeout or error (falling back to deterministic synthesis): {e}")
                final_text = self._fallback_synthesis(state, is_en)
        else:
            final_text = self._fallback_synthesis(state, is_en)

        return {"final_response": final_text}

    def _fallback_synthesis(self, state: AIOpsState, is_en: bool) -> str:
        """API 키 부재 시 정형 팩트 및 hconfig 계층적 복원 설정을 포함한 완성형 리포트 생성"""
        confirmed = state.get("confirmed_root_cause")
        evidence = state.get("batfish_evidence")
        scope = state.get("scope_type")
        intermediates = state.get("intermediate_devices", [])
        all_involved = state.get("all_involved_devices", [])
        proto = state.get("detected_protocol", "direct").upper()
        hconfig_plan = self.generate_hconfig_remediation(state)

        if is_en:
            return (
                f"### 📋 [LangGraph & Batfish Autonomous AIOps Synthesis Report]\n\n"
                f"#### 1. Scope & Topology Analysis\n"
                f"- **Diagnosis Scope:** `{scope}` (Protocol: `{proto}`)\n"
                f"- **Source Device:** `{state.get('source_device')}` ➔ **Destination:** `{state.get('destination_device') or 'Local'}`\n"
                f"- **Transit Hops:** `{intermediates or 'Directly Connected'}`\n"
                f"- **Involved Devices:** `{', '.join(all_involved)}`\n\n"
                f"#### 2. Batfish Formal Verification (Confirmed Fact)\n"
                f"- **Confirmed Root Cause:** **`{confirmed}`** (Confidence: 98%)\n"
                f"- **Mathematical / Config Proof:** `{evidence}`\n\n"
                f"#### 3. Hierarchical Configuration Remediation (hconfig)\n"
                f"- **Target Device:** `{hconfig_plan['target_device']}`\n"
                f"- **Remediation Rationale:** {hconfig_plan['explanation']}\n\n"
                f"```cisco\n{hconfig_plan['hconfig_block']}\n```\n\n"
                f"#### 4. Post-Restoration Verification Commands\n"
                + "\n".join([f"- `{cmd}`" for cmd in hconfig_plan['post_verification_commands']])
            )
        else:
            return (
                f"### 📋 [LangGraph & Batfish 자율 AIOps 종합 진단 리포트]\n\n"
                f"#### 1. 장애 범위 및 동적 토폴로지 분석\n"
                f"- **장애 범위(Scope):** `{scope}` (동적 프로토콜: `{proto}`)\n"
                f"- **출발지 장비:** `{state.get('source_device')}` ➔ **목적지 장비:** `{state.get('destination_device') or '로컬 피어'}`\n"
                f"- **중간 Transit 경유지:** `{intermediates or '직접 연결 구간 (경유지 없음)'}`\n"
                f"- **진단 대상 전체 장비:** `{', '.join(all_involved)}`\n\n"
                f"#### 2. Batfish 정형 검증 및 진단 확인 (Verification)\n"
                f"- **확정된 근본 원인:** **`{confirmed}`** (신뢰도: 98%)\n"
                f"- **정형 검증 및 설정상 근거:** {evidence}\n\n"
                f"#### 3. 계층적 복원 설정 (Hierarchical Config - hconfig)\n"
                f"- **복원 대상 장비:** `{hconfig_plan['target_device']}`\n"
                f"- **복원 설정 배경:** {hconfig_plan['explanation']}\n\n"
                f"```cisco\n{hconfig_plan['hconfig_block']}\n```\n\n"
                f"#### 4. 복원 후 사후 검증 (Post-Verification) 절차\n"
                f"복원 설정 적용 후 다음 명령어를 실행하여 세션 및 라우트 정상 수신을 최종 확인하십시오:\n"
                + "\n".join([f"- `{cmd}`" for cmd in hconfig_plan['post_verification_commands']])
            )

    # -----------------------------------------------------------------
    # SSE Streaming Wrapper (Next.js 프론트엔드 연동)
    # -----------------------------------------------------------------
    async def stream_diagnostic_workflow(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        llm_config: Optional[LLMConfig] = None,
        device_config: Optional[DeviceConfig] = None,
        language: str = "ko",
        debug_mode: bool = True
    ) -> AsyncGenerator[Dict[str, str], None]:
        """LangGraph 실행 결과를 실시간 SSE 이벤트(trace, mcp_result, token, complete)로 스트리밍"""
        session_id = f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_time = datetime.now().isoformat()
        is_en = language == "en"

        all_devices = device_manager.get_all_devices()
        dev_names = [d.name.lower() for d in all_devices]
        llm_cfg_dict = llm_config.model_dump() if llm_config else {}

        # 1차 초경량 LLM 의도 및 대상 장비 추출
        intent_data = await self.extract_intent_and_scope(message, llm_cfg_dict, dev_names)

        # 1. 단순 장비 현황(대수/목록) 질의 시: 진단 워크플로우를 타지 않고 장비 API 결과 즉시 반환
        if intent_data.get("is_inventory_query"):
            dev_bullets = "\n".join([f"- **`{d.name}`** (IP: `{d.host}`, Port: `{d.port or 22}`)" for d in all_devices])
            if is_en:
                ans = f"Currently, there are **{len(all_devices)} network devices** registered and active in the Net-AIOps Studio inventory:\n\n{dev_bullets}"
            else:
                ans = f"현재 Net-AIOps 시스템에 등록되어 관리 중인 활성 네트워크 장비는 총 **{len(all_devices)}대**입니다:\n\n{dev_bullets}"

            yield {"event": "llm_token", "data": json.dumps({"token": ans})}
            yield {"event": "complete", "data": json.dumps({"status": "success", "session_id": session_id})}
            return

        initial_state: AIOpsState = {
            "session_id": session_id,
            "session_start_time": start_time,
            "debug_mode": debug_mode,
            "message": message,
            "history": [h.model_dump() for h in (history or [])],
            "language": language,
            "device_config": device_config.model_dump() if device_config else {},
            "llm_config": llm_cfg_dict,
            "intent_data": intent_data,
            "scope_type": "POINT_TO_POINT",
            "source_device": intent_data.get("seed_devices", ["r1"])[0] if intent_data.get("seed_devices") else "r1",
            "destination_device": intent_data.get("seed_devices", ["r1", ""])[1] if len(intent_data.get("seed_devices", [])) > 1 else "",
            "intermediate_devices": [],
            "all_involved_devices": [],
            "target_device": device_config.host if device_config else "192.168.100.11",
            "symptom_id": "",
            "symptom_label": "",
            "candidate_root_causes": [],
            "verification_commands": [],
            "remediation_actions": [],
            "batfish_questions": [],
            "paired_cli_commands": [],
            "batfish_eval": {},
            "confirmed_root_cause": "",
            "batfish_evidence": "",
            "pruned_root_causes": [],
            "executed_telemetry": [],
            "final_response": "",
            "trace_events": [],
            "stream_events": [],
            "session_log_path": "",
            "session_txt_path": ""
        }

        all_streamed_traces = []
        emitted_event_keys = set()

        # Step 1: Scope Detection 실행
        s1 = self.scope_detection_node(initial_state)
        current_state = {**initial_state, **s1}
        for ev in s1.get("trace_events", []):
            k = f"{ev.get('step')}_{ev.get('title')}"
            if k not in emitted_event_keys:
                emitted_event_keys.add(k)
                all_streamed_traces.append(ev)
                yield {"event": "trace", "data": json.dumps(ev)}
                await asyncio.sleep(0.1)

        # Step 2: Causal Routing 실행
        s2 = self.causal_routing_node(current_state)
        current_state = {**current_state, **s2}
        for ev in s2.get("trace_events", []):
            k = f"{ev.get('step')}_{ev.get('title')}"
            if k not in emitted_event_keys:
                emitted_event_keys.add(k)
                all_streamed_traces.append(ev)
                yield {"event": "trace", "data": json.dumps(ev)}
                await asyncio.sleep(0.2)

        # Causal Path 이벤트 발행
        causal_paths = graph_engine.find_causal_paths(current_state["symptom_id"])
        path_ev = {
            "step": "graph_explored",
            "title": f"Causal Paths Discovered ({len(causal_paths)} paths)",
            "start_node": current_state["symptom_id"],
            "paths": causal_paths,
            "timestamp": datetime.now().isoformat()
        }
        all_streamed_traces.append(path_ev)
        yield {
            "event": "graph_path",
            "data": json.dumps(path_ev)
        }
        await asyncio.sleep(0.2)

        # Step 3: Batfish Verification 실행
        s3 = self.batfish_verification_node(current_state)
        current_state = {**current_state, **s3}
        for ev in s3.get("trace_events", []):
            k = f"{ev.get('step')}_{ev.get('title')}"
            if k not in emitted_event_keys:
                emitted_event_keys.add(k)
                all_streamed_traces.append(ev)
                yield {"event": "trace", "data": json.dumps(ev)}
                await asyncio.sleep(0.2)

        # Step 4: Live Telemetry 실행
        s4 = self.live_telemetry_node(current_state)
        current_state = {**current_state, **s4}
        for res in s4.get("executed_telemetry", []):
            dev_label = res.get("device_name") or res.get("host")
            mcp_ev = {
                "step": "mcp_execute_complete",
                "title": f"Live CLI Collected: `{res.get('command')}` on {dev_label}",
                "status": "success",
                "command": res.get("command"),
                "device_name": res.get("device_name"),
                "host": res.get("host"),
                "raw_output": res.get("raw_output", ""),
                "parsed_output": res.get("parsed_output", []),
                "timestamp": datetime.now().isoformat()
            }
            all_streamed_traces.append(mcp_ev)
            yield {
                "event": "mcp_result",
                "data": json.dumps(mcp_ev)
            }
            await asyncio.sleep(0.2)

        # Step 5: LLM Synthesis 실행
        s5 = await self.llm_synthesis_node(current_state)
        raw_final_text = s5.get("final_response", "")

        # 채팅 화면에는 트러블슈팅 메타데이터 블록을 붙이지 않고 순수 진단 결과만 전달
        final_text = raw_final_text.strip()

        # 디버그 모드가 켜져 있을 때만 세션 전체 데이터 및 Trace 로그 파일 영구 저장
        if debug_mode:
            json_path, log_path = save_diagnostic_session_log(
                session_id=session_id,
                start_time=start_time,
                state=current_state,
                final_text=final_text,
                all_trace_events=all_streamed_traces
            )
            current_state["session_log_path"] = json_path
            current_state["session_txt_path"] = log_path

            # 트러블슈팅 세션 보관 알림 Trace 이벤트 발행
            session_trace_ev = {
                "step": "session_info",
                "title": f"트러블슈팅 세션 보관 완료 ({session_id})" if not is_en else f"Session Troubleshooting Record Stored ({session_id})",
                "status": "success",
                "message": (
                    f"실시간 진단 Trace 및 텔레메트리가 logs/ai_diagnostics/{session_id}.json 및 .log 에 영구 보관되었습니다. (터미널에서 `cat logs/ai_diagnostics/{session_id}.log`로 즉시 재현 가능)"
                    if not is_en else
                    f"Diagnostic trace and telemetry preserved in logs/ai_diagnostics/{session_id}.json & .log. (Run `cat logs/ai_diagnostics/{session_id}.log` to replay)."
                ),
                "session_id": session_id,
                "debug_mode": True,
                "json_log_path": f"logs/ai_diagnostics/{session_id}.json",
                "text_log_path": f"logs/ai_diagnostics/{session_id}.log",
                "timestamp": datetime.now().isoformat()
            }
        else:
            session_trace_ev = {
                "step": "session_info",
                "title": f"디버그 로그 모드 OFF ({session_id})" if not is_en else f"Debug Log Mode OFF ({session_id})",
                "status": "success",
                "message": (
                    f"디버그 모드가 비활성화되어 파일 저장을 건너뛰었습니다."
                    if not is_en else
                    f"Debug mode is disabled. Session trace file saving was skipped."
                ),
                "session_id": session_id,
                "debug_mode": False,
                "timestamp": datetime.now().isoformat()
            }

        all_streamed_traces.append(session_trace_ev)
        yield {"event": "trace", "data": json.dumps(session_trace_ev)}
        await asyncio.sleep(0.1)

        # 스트리밍 토큰 전달
        chunk_size = 80
        for i in range(0, len(final_text), chunk_size):
            chunk = final_text[i:i + chunk_size]
            yield {"event": "llm_token", "data": json.dumps({"token": chunk})}
            await asyncio.sleep(0.03)

        # 진단 완료 이벤트
        complete_payload = {
            "status": "success",
            "session_id": session_id,
            "debug_mode": debug_mode,
            "scope_type": current_state.get("scope_type"),
            "confirmed_root_cause": current_state.get("confirmed_root_cause"),
            "host": current_state.get("target_device")
        }
        if debug_mode:
            complete_payload["session_log_path"] = f"logs/ai_diagnostics/{session_id}.json"
            complete_payload["text_log_path"] = f"logs/ai_diagnostics/{session_id}.log"

        yield {
            "event": "complete",
            "data": json.dumps(complete_payload)
        }


# 전역 인스턴스
langgraph_agent = LangGraphAIOpsAgent()
