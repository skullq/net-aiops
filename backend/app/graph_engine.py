import logging
from typing import Any, Dict, List, Optional
import networkx as nx

from app.models import EdgeModel, NodeModel, NodeType

logger = logging.getLogger(__name__)


class CausalGraphEngine:
    """NetworkX DiGraph 기반 인과관계(Causal Graph) 분석 및 관리 엔진.

    노드 타입:
    - Symptom: 네트워크 이상 증상 (예: BGP Down, 패킷 드롭)
    - RootCause: 근본 원인 (예: MTU 불일치, 비밀번호 오류)
    - Verification: 원인 확인 및 검증 절차 (예: 상태 점검 단계)
    - Command: 진단/확인 및 복구에 필요한 구체적 CLI 명령어
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.reset_to_default()

    def reset_to_default(self) -> None:
        """기본 Cisco IOS-XE 장애 진단 인과 그래프 데이터로 초기화합니다."""
        self.graph.clear()

        # 기본 노드 정의
        default_nodes = [
            # 1. BGP Down 시나리오
            NodeModel(
                id="symptom_bgp_down",
                label="BGP Neighbor Down",
                type=NodeType.SYMPTOM,
                description="BGP 피어 연결이 끊어지거나 Idle/Active 상태로 머무름",
                details={"severity": "CRITICAL", "category": "Routing"}
            ),
            NodeModel(
                id="rc_bgp_auth_mismatch",
                label="BGP MD5 Password Mismatch",
                type=NodeType.ROOT_CAUSE,
                description="BGP 피어 간 MD5 패스워드 불일치로 인한 TCP 세션 수립 실패",
                details={"protocol": "BGP", "layer": "L4-L7"}
            ),
            NodeModel(
                id="rc_bgp_mtu_mismatch",
                label="Interface MTU Mismatch",
                type=NodeType.ROOT_CAUSE,
                description="피어 인터페이스 간 MTU 크기 불일치로 큰 패킷 전송 시 세션 리셋",
                details={"protocol": "IP/Ethernet", "layer": "L2-L3"}
            ),
            NodeModel(
                id="rc_interface_flapping",
                label="Physical Link Flapping",
                type=NodeType.ROOT_CAUSE,
                description="물리 인터페이스 불안정 또는 CRC 에러로 인한 링크 플래핑",
                details={"protocol": "Ethernet", "layer": "L1-L2"}
            ),
            NodeModel(
                id="ver_check_bgp_summary",
                label="Verify BGP Summary",
                type=NodeType.VERIFICATION,
                description="BGP 네이버 상태 및 접두사(Prefix) 수신 상태 확인",
                details={"method": "CLI Verification"}
            ),
            NodeModel(
                id="cmd_show_ip_bgp_summary",
                label="show ip bgp summary",
                type=NodeType.COMMAND,
                description="BGP 요약 정보 확인",
                details={"command": "show ip bgp summary", "expected_state": "Established"}
            ),
            NodeModel(
                id="ver_check_bgp_neighbors",
                label="Inspect BGP Neighbor Log",
                type=NodeType.VERIFICATION,
                description="BGP 네이버 상세 에러 코드(Notification) 및 재연결 횟수 조사",
                details={"method": "Detailed CLI Log Check"}
            ),
            NodeModel(
                id="cmd_show_ip_bgp_neighbors",
                label="show ip bgp neighbors",
                type=NodeType.COMMAND,
                description="BGP 네이버 상세 정보 및 통계 확인",
                details={"command": "show ip bgp neighbors"}
            ),
            NodeModel(
                id="ver_check_interface_status",
                label="Verify Interface Status",
                type=NodeType.VERIFICATION,
                description="물리 인터페이스 링크 및 프로토콜 상태(Up/Up) 확인",
                details={"method": "Interface State Inspection"}
            ),
            NodeModel(
                id="cmd_show_ip_int_brief",
                label="show ip interface brief",
                type=NodeType.COMMAND,
                description="전체 인터페이스 IP 및 Line Status 확인",
                details={"command": "show ip interface brief"}
            ),
            NodeModel(
                id="cmd_fix_bgp_auth",
                label="Remediation: Fix BGP Auth",
                type=NodeType.COMMAND,
                description="BGP 피어 MD5 패스워드 재설정 및 동기화",
                details={"type": "Remediation", "action": "hier_config_patch"}
            ),
            NodeModel(
                id="cmd_fix_interface_mtu",
                label="Remediation: Set MTU 1500",
                type=NodeType.COMMAND,
                description="인터페이스 MTU를 표준 1500으로 복구",
                details={"type": "Remediation", "action": "hier_config_patch"}
            ),

            # 2. OSPF ExStart 시나리오
            NodeModel(
                id="symptom_ospf_exstart",
                label="OSPF Stuck in ExStart",
                type=NodeType.SYMPTOM,
                description="OSPF 네이버 상태가 DBD 교환 단계(ExStart/Exchange)에 고착됨",
                details={"severity": "HIGH", "category": "Routing"}
            ),
            NodeModel(
                id="rc_ospf_mtu_mismatch",
                label="OSPF MTU Mismatch",
                type=NodeType.ROOT_CAUSE,
                description="양단 인터페이스 MTU가 일치하지 않아 DBD 수신 실패",
                details={"protocol": "OSPF", "layer": "L3"}
            ),
            NodeModel(
                id="ver_check_ospf_neighbor",
                label="Verify OSPF Neighbor",
                type=NodeType.VERIFICATION,
                description="OSPF 인접 관계 상태 및 데드 타이머 점검",
                details={"method": "OSPF CLI Verification"}
            ),
            NodeModel(
                id="cmd_show_ip_ospf_neighbor",
                label="show ip ospf neighbor",
                type=NodeType.COMMAND,
                description="OSPF 네이버 상태 및 인터페이스 확인",
                details={"command": "show ip ospf neighbor"}
            ),
            NodeModel(
                id="cmd_fix_ospf_mtu",
                label="Remediation: OSPF MTU Ignore",
                type=NodeType.COMMAND,
                description="해당 인터페이스에 'ip ospf mtu-ignore' 설정 또는 MTU 일치화",
                details={"type": "Remediation", "action": "cli_remediation"}
            ),

            # 3. Interface CRC Errors 시나리오
            NodeModel(
                id="symptom_input_errors",
                label="Interface Input/CRC Errors",
                type=NodeType.SYMPTOM,
                description="인터페이스 입력 에러 및 CRC 카운터 급증으로 패킷 드롭 발생",
                details={"severity": "MEDIUM", "category": "Hardware/L2"}
            ),
            NodeModel(
                id="rc_duplex_mismatch",
                label="Duplex Mismatch (Half/Full)",
                type=NodeType.ROOT_CAUSE,
                description="대향 장비와의 Duplex 설정 불일치로 인한 Late Collision",
                details={"protocol": "Ethernet", "layer": "L2"}
            ),
            NodeModel(
                id="ver_check_interface_counters",
                label="Inspect Interface Counters",
                type=NodeType.VERIFICATION,
                description="에러 카운터, Collision 및 Duplex 상태 점검",
                details={"method": "Detailed Interface Stats"}
            ),
            NodeModel(
                id="cmd_show_interfaces",
                label="show interfaces",
                type=NodeType.COMMAND,
                description="인터페이스 상세 카운터 및 Duplex 모드 점검",
                details={"command": "show interfaces GigabitEthernet1"}
            ),
            NodeModel(
                id="cmd_fix_duplex_auto",
                label="Remediation: Auto Duplex/Speed",
                type=NodeType.COMMAND,
                description="인터페이스를 speed auto 및 duplex auto 로 복구",
                details={"type": "Remediation", "action": "hier_config_patch"}
            )
        ]

        for node in default_nodes:
            self.add_node(node)

        # 기본 엣지 정의
        default_edges = [
            # BGP 관계
            EdgeModel(source="symptom_bgp_down", target="rc_bgp_auth_mismatch", relationship="caused_by"),
            EdgeModel(source="symptom_bgp_down", target="rc_bgp_mtu_mismatch", relationship="caused_by"),
            EdgeModel(source="symptom_bgp_down", target="rc_interface_flapping", relationship="caused_by"),
            EdgeModel(source="symptom_bgp_down", target="ver_check_bgp_summary", relationship="diagnose_with"),
            EdgeModel(source="ver_check_bgp_summary", target="cmd_show_ip_bgp_summary", relationship="executes"),
            EdgeModel(source="rc_bgp_auth_mismatch", target="ver_check_bgp_neighbors", relationship="verified_by"),
            EdgeModel(source="ver_check_bgp_neighbors", target="cmd_show_ip_bgp_neighbors", relationship="executes"),
            EdgeModel(source="rc_interface_flapping", target="ver_check_interface_status", relationship="verified_by"),
            EdgeModel(source="ver_check_interface_status", target="cmd_show_ip_int_brief", relationship="executes"),
            EdgeModel(source="rc_bgp_auth_mismatch", target="cmd_fix_bgp_auth", relationship="mitigated_by"),
            EdgeModel(source="rc_bgp_mtu_mismatch", target="cmd_fix_interface_mtu", relationship="mitigated_by"),

            # OSPF 관계
            EdgeModel(source="symptom_ospf_exstart", target="rc_ospf_mtu_mismatch", relationship="caused_by"),
            EdgeModel(source="symptom_ospf_exstart", target="ver_check_ospf_neighbor", relationship="diagnose_with"),
            EdgeModel(source="ver_check_ospf_neighbor", target="cmd_show_ip_ospf_neighbor", relationship="executes"),
            EdgeModel(source="rc_ospf_mtu_mismatch", target="cmd_fix_ospf_mtu", relationship="mitigated_by"),

            # Interface Errors 관계
            EdgeModel(source="symptom_input_errors", target="rc_duplex_mismatch", relationship="caused_by"),
            EdgeModel(source="symptom_input_errors", target="ver_check_interface_counters", relationship="diagnose_with"),
            EdgeModel(source="ver_check_interface_counters", target="cmd_show_interfaces", relationship="executes"),
            EdgeModel(source="rc_duplex_mismatch", target="cmd_fix_duplex_auto", relationship="mitigated_by"),
        ]

        for edge in default_edges:
            self.add_edge(edge)

        logger.info(f"Default Causal Graph initialized with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")

    def add_node(self, node: NodeModel) -> None:
        """노드를 추가하거나 기존 노드를 업데이트합니다."""
        self.graph.add_node(
            node.id,
            label=node.label,
            type=node.type.value if hasattr(node.type, "value") else str(node.type),
            description=node.description or "",
            details=node.details or {}
        )

    def delete_node(self, node_id: str) -> bool:
        """노드 및 연결된 엣지를 삭제합니다."""
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)
            return True
        return False

    def add_edge(self, edge: EdgeModel) -> None:
        """방향성 엣지를 추가합니다. (source -> target)"""
        if not self.graph.has_node(edge.source):
            # 미등록 노드 자동 생성
            self.graph.add_node(edge.source, label=edge.source, type=NodeType.SYMPTOM.value, description="", details={})
        if not self.graph.has_node(edge.target):
            self.graph.add_node(edge.target, label=edge.target, type=NodeType.ROOT_CAUSE.value, description="", details={})

        self.graph.add_edge(
            edge.source,
            edge.target,
            relationship=edge.relationship or "leads_to",
            description=edge.description or ""
        )

    def delete_edge(self, source: str, target: str) -> bool:
        """지정된 두 노드 간의 엣지를 삭제합니다."""
        if self.graph.has_edge(source, target):
            self.graph.remove_edge(source, target)
            return True
        return False

    def get_graph_data(self) -> Dict[str, Any]:
        """react-force-graph-2d 호환 JSON 형식으로 그래프 데이터를 반환합니다."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", NodeType.SYMPTOM.value),
                "description": attrs.get("description", ""),
                "details": attrs.get("details", {})
            })

        links = []
        for src, dst, attrs in self.graph.edges(data=True):
            links.append({
                "source": src,
                "target": dst,
                "relationship": attrs.get("relationship", "leads_to"),
                "description": attrs.get("description", "")
            })

        return {
            "nodes": nodes,
            "links": links
        }

    def find_causal_paths(self, start_node_id: str) -> List[Dict[str, Any]]:
        """특정 노드에서 도달 가능한 모든 인과 관계 경로를 탐색합니다."""
        if not self.graph.has_node(start_node_id):
            return []

        paths = []
        # DFS를 활용한 모든 경로 탐색 (최대 깊이 6 제한)
        for target_node in self.graph.nodes:
            if target_node != start_node_id and nx.has_path(self.graph, start_node_id, target_node):
                for p in nx.all_simple_paths(self.graph, source=start_node_id, target=target_node, cutoff=6):
                    path_details = []
                    for nid in p:
                        attrs = self.graph.nodes[nid]
                        path_details.append({
                            "id": nid,
                            "label": attrs.get("label", nid),
                            "type": attrs.get("type")
                        })
                    paths.append({
                        "path": p,
                        "steps": path_details
                    })
        return paths

    def query_subgraph_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """키워드가 포함된 노드와 그 1-hop 및 2-hop 이웃 서브그래프를 반환합니다."""
        matched_node_ids = set()
        keyword_lower = keyword.lower()

        for node_id, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", "").lower()
            desc = attrs.get("description", "").lower()
            if keyword_lower in node_id.lower() or keyword_lower in label or keyword_lower in desc:
                matched_node_ids.add(node_id)

        # 1-hop 이웃 확장
        subgraph_nodes = set(matched_node_ids)
        for n in matched_node_ids:
            subgraph_nodes.update(self.graph.predecessors(n))
            subgraph_nodes.update(self.graph.successors(n))

        sub_g = self.graph.subgraph(subgraph_nodes)
        
        nodes = []
        for node_id, attrs in sub_g.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", NodeType.SYMPTOM.value),
                "description": attrs.get("description", ""),
                "details": attrs.get("details", {})
            })

        links = []
        for src, dst, attrs in sub_g.edges(data=True):
            links.append({
                "source": src,
                "target": dst,
                "relationship": attrs.get("relationship", "leads_to"),
                "description": attrs.get("description", "")
            })

        return {
            "matched_count": len(matched_node_ids),
            "nodes": nodes,
            "links": links
        }

    def get_context_for_llm(self) -> str:
        """LLM 시스템 프롬프트에 주입할 Causal Graph 요약 텍스트를 생성합니다."""
        summary = ["### Network-AIOps Causal Diagnostic Knowledge Graph ###"]
        for node_id, attrs in self.graph.nodes(data=True):
            ntype = attrs.get("type", "Node")
            label = attrs.get("label", node_id)
            desc = attrs.get("description", "")
            successors = [f"{s}({self.graph.nodes[s].get('label', s)})" for s in self.graph.successors(node_id)]
            succ_str = f" -> leads to: {', '.join(successors)}" if successors else ""
            summary.append(f"- [{ntype}] {label} (ID: {node_id}): {desc}{succ_str}")
        return "\n".join(summary)


# 싱글톤 인스턴스
graph_engine = CausalGraphEngine()
