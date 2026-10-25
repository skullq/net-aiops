import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import networkx as nx

from app.models import EdgeModel, NodeModel, NodeType

logger = logging.getLogger(__name__)


class BaseGraphAdapter:
    """미래 Neo4j 및 ArangoDB 이전을 위한 추상 그래프 저장소 인터페이스"""
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    def sync_from_storage(self) -> None:
        raise NotImplementedError

    def export_data(self) -> Dict[str, Any]:
        raise NotImplementedError


class UniversalCausalGraphEngine:
    """탈중앙화 및 Neo4j / ArangoDB 전환 호환 인과 그래프 엔진.
    
    특징:
    1. 데이터 저장소 분리: `causal_graph.json` (ArangoDB Document/Edge 컬렉션 호환) 및 `causal_graph.cypher` (Neo4j openCypher 호환) 동시 동기화.
    2. Zero-Lock 인메모리 NetworkX DiGraph 기반 고속 탐색 및 실시간 시각화 API 제공.
    3. Neo4j Bolt 드라이버 및 ArangoDB AQL 연동을 위한 어댑터 확장성 내장.
    4. OSI 7 Layer (Bottom-Up) 계층별 검증 명령어 자동 정렬 기능 유지.
    """

    def __init__(
        self,
        json_file_path: Optional[str] = None,
        cypher_file_path: Optional[str] = None
    ):
        self.graph = nx.DiGraph()
        self.json_file_path = json_file_path or str(Path(__file__).parent / "causal_graph.json")
        self.cypher_file_path = cypher_file_path or str(Path(__file__).parent / "causal_graph.cypher")
        self.reset_to_default()

    def reset_to_default(self) -> None:
        """분리된 데이터 파일(JSON 및 Cypher)로부터 그래프 데이터를 로드하고 정규화/인과연결을 적용합니다."""
        if Path(self.json_file_path).exists():
            self._load_from_json(self.json_file_path)
        elif Path(self.cypher_file_path).exists():
            self._load_from_cypher(self.cypher_file_path)
        else:
            logger.warning("No seed graph files found. Starting with empty graph.")

        # 중복 명령어 노드 통합 및 고립 인과 엣지 자동 복구 파이프라인 가동
        self.canonicalize_and_repair_graph(save=True)

    def canonicalize_and_repair_graph(self, save: bool = True) -> Dict[str, Any]:
        """모든 GraphDB 생성/로드 시 자동으로 중복 명령어를 단일 허브로 통합하고 고립 인과 링크를 복구합니다.
        
        규칙:
        1. 동일한 CLI 명령어(label 및 command)를 가진 복수 Command 노드를 단일 대표(Canonical) 노드로 수렴.
        2. 중복 노드로 향하던 모든 검증(Verification) 엣지의 타겟을 대표 노드로 재연결.
        3. 고립된 컴포넌트(BGP Active, Flapping, OSPF)를 메인 인과 체인에 결속.
        """
        # 1. 중복 명령어 매핑 사전 (중복 노드 ID -> 대표 Canonical 노드 ID)
        canonical_map: Dict[str, str] = {
            # show running-config 통합 -> cmd_show_running_config
            "cmd_pair_initIssues": "cmd_show_running_config",
            "cmd_pair_parseWarning": "cmd_show_running_config",
            "cmd_pair_undefinedReferences": "cmd_show_running_config",
            "cmd_pair_unusedStructures": "cmd_show_running_config",
            "cmd_pair_viConversionWarning": "cmd_show_running_config",
            "cmd_pair_namedStructures": "cmd_show_running_config",
            "cmd_show_run_int": "cmd_show_running_config",

            # show ip interface brief 통합 -> cmd_show_ip_int_brief
            "cmd_pair_layer3Edges": "cmd_show_ip_int_brief",
            "cmd_pair_ipOwners": "cmd_show_ip_int_brief",
            "cmd_pair_resolveInterfaceSpecifier": "cmd_show_ip_int_brief",
            "cmd_pair_resolveLocationSpecifier": "cmd_show_ip_int_brief",
            "cmd_pair_resolveIpsOfLocationSpecifier": "cmd_show_ip_int_brief",

            # show ip ospf neighbor 통합 -> cmd_show_ip_ospf_neighbor
            "cmd_pair_ospfEdges": "cmd_show_ip_ospf_neighbor",
            "cmd_pair_ospfSessionCompatibility": "cmd_show_ip_ospf_neighbor",

            # show ip bgp summary 통합 -> cmd_show_ip_bgp_summary
            "cmd_pair_bgpEdges": "cmd_show_ip_bgp_summary",
            "cmd_pair_bgpSessionStatus": "cmd_show_ip_bgp_summary",

            # show ip bgp neighbors 통합 -> cmd_show_ip_bgp_neighbors
            "cmd_pair_bgpPeerConfiguration": "cmd_show_ip_bgp_neighbors",
            "cmd_pair_bgpSessionCompatibility": "cmd_show_ip_bgp_neighbors",

            # show route-map 통합 -> cmd_show_route_map
            "cmd_pair_searchRoutePolicies": "cmd_show_route_map",
            "cmd_pair_testRoutePolicies": "cmd_show_route_map",

            # show archive config differences 통합 -> cmd_show_archive_config_diff
            "cmd_pair_compareFilters": "cmd_pair_differentialReachability",
            "cmd_pair_compareRoutePolicies": "cmd_pair_differentialReachability",

            # show ip access-lists 통합 -> cmd_pair_filterLineReachability
            "cmd_pair_searchFilters": "cmd_pair_filterLineReachability",
            "cmd_pair_resolveFilterSpecifier": "cmd_pair_filterLineReachability",

            # show running-config | section router bgp 통합 -> cmd_show_run_bgp
            "cmd_pair_bgpProcessConfiguration": "cmd_show_run_bgp",

            # show ip bgp 통합 -> cmd_show_ip_bgp_prefix
            "cmd_pair_bgpRib": "cmd_show_ip_bgp_prefix",

            # show isis neighbors 통합 -> cmd_show_isis_neighbors
            "cmd_pair_isisEdges": "cmd_show_isis_neighbors",

            # show ip ospf 통합 -> cmd_pair_ospfAreaConfiguration
            "cmd_pair_ospfProcessConfiguration": "cmd_pair_ospfAreaConfiguration",

            # show ip route 통합 -> cmd_pair_routes
            "cmd_pair_resolveIpSpecifier": "cmd_pair_routes",

            # traceroute 통합 -> cmd_pair_traceroute
            "cmd_pair_bidirectionalTraceroute": "cmd_pair_traceroute",

            # show cdp neighbors detail 통합 -> cmd_pair_edges
            "cmd_pair_userProvidedLayer1Edges": "cmd_pair_edges",

            # show version 통합 -> cmd_pair_nodeProperties
            "cmd_pair_viConversionStatus": "cmd_pair_nodeProperties",

            # help 통합 -> cmd_pair_list
            "cmd_pair_list_tags": "cmd_pair_list",
        }

        # 대표 노드 존재 보장
        if not self.graph.has_node("cmd_show_running_config"):
            self.graph.add_node(
                "cmd_show_running_config",
                label="show running-config",
                type="Command",
                description="전체 Cisco IOS-XE 활성 러닝 설정 확인",
                details={"command": "show running-config", "layer": "Layer 7 (Application / Configuration)"}
            )

        merged_nodes_count = 0
        redirected_edges_count = 0

        # 엣지 재연결 (중복 노드로 향하는 엣지를 대표 노드로 변경)
        edges_to_remove = []
        edges_to_add = []

        for u, v, d in self.graph.edges(data=True):
            target_canonical = canonical_map.get(v)
            if target_canonical:
                edges_to_remove.append((u, v))
                edges_to_add.append((u, target_canonical, d))

        for u, v in edges_to_remove:
            self.graph.remove_edge(u, v)

        for u, v, d in edges_to_add:
            if not self.graph.has_edge(u, v):
                self.graph.add_edge(u, v, **d)
                redirected_edges_count += 1

        # 중복 노드 삭제
        for dup_id in canonical_map.keys():
            if self.graph.has_node(dup_id):
                self.graph.remove_node(dup_id)
                merged_nodes_count += 1

        # IS-IS 언더레이 장애 및 Metric-Style 불일치 인과 노드 보장
        isis_nodes = [
            ("symptom_isis_underlay_down", "IS-IS Underlay Route Down", "Symptom", "IS-IS 언더레이 라우트 미수신 또는 인접성/IP 도달성 결손 장애"),
            ("rc_isis_metric_style_mismatch", "IS-IS Metric-Style Mismatch", "RootCause", "IS-IS Narrow vs Wide Metric-Style TLV 불일치로 인한 IP 도달성(Reachability) 접두사 교환 실패"),
            ("verif_isis_metric_style", "Verify IS-IS Metric Style & TLVs", "Verification", "IS-IS metric-style 및 TLV 128/135 교환 여부 검증"),
            ("remed_isis_metric_style", "router isis / metric-style wide", "Remediation", "router isis 설정 하위에 metric-style wide 명령어를 일관되게 적용하여 TLV 135 기반 확장 IP 도달성 교환 활성화"),
            ("cmd_show_run_isis", "show running-config | section router isis", "Command", "IS-IS 프로세스 및 metric-style 설정 확인"),
            ("cmd_show_ip_route_isis", "show ip route isis", "Command", "IS-IS를 통해 수신된 IPv4 라우트 테이블 확인"),
        ]
        for nid, nlabel, ntype, ndesc in isis_nodes:
            if not self.graph.has_node(nid):
                self.graph.add_node(nid, label=nlabel, type=ntype, description=ndesc, details={"cli_command": nlabel if ntype == "Command" else ""})

        # 2. 도메인 간 인과 연결(Cross-Domain Causal Links) 보강
        added_causal_links = 0
        critical_cross_links = [
            # OSPF 및 BGP 세션 장애를 유발하는 인터페이스 ACL 차단 인과 체인
            ("symptom_ospf_down", "rc_interface_acl_blocked", "leads_to", "인터페이스 ACL 차단으로 인한 OSPF 제어 트래픽 차단 및 네이버 불능"),
            ("symptom_bgp_down", "rc_interface_acl_blocked", "leads_to", "인터페이스 ACL 차단으로 인한 BGP TCP 179 포트 제어 트래픽 차단"),
            # OSPF 네이버 다운은 BGP 언더레이 넥스트홉 결손의 직접 원인
            ("symptom_ospf_down", "rc_bgp_nexthop_missing_ospf", "leads_to", "OSPF 언더레이 인접성 붕괴로 인한 BGP Next-Hop 도달 불가 유발"),
            # BGP Stuck in Active 는 BGP 세션 다운 상태를 초래
            ("symptom_bgp_active", "symptom_bgp_down", "leads_to", "BGP Active 상태 장기화는 BGP 세션 다운 유발"),
            # BGP Session Flapping 은 BGP 세션 불안정 및 다운 초래
            ("symptom_bgp_flapping", "symptom_bgp_down", "leads_to", "지속적 세션 플래핑으로 인한 세션 인접성 상실"),
            # IS-IS 인과 체인
            ("symptom_isis_underlay_down", "rc_isis_metric_style_mismatch", "caused_by", "IS-IS Metric-Style TLV 불일치로 인한 라우트 도달 불가"),
            ("rc_isis_metric_style_mismatch", "verif_isis_metric_style", "verified_by", "IS-IS Metric Style 및 TLV 교환 상태 검증"),
            ("verif_isis_metric_style", "cmd_show_run_isis", "executes_cli", "IS-IS 설정 CLI 검증"),
            ("verif_isis_metric_style", "cmd_show_isis_neighbors", "executes_cli", "IS-IS 인접성 상태 검증"),
            ("verif_isis_metric_style", "cmd_show_ip_route_isis", "executes_cli", "IS-IS 라우트 수신 여부 검증"),
            ("rc_isis_metric_style_mismatch", "remed_isis_metric_style", "remediated_by", "metric-style wide 설정 통일 복구 조치"),
            # IS-IS 언더레이 장애 또한 BGP 다운과 유기적 연결
            ("symptom_isis_underlay_down", "symptom_bgp_down", "leads_to", "IS-IS 언더레이 결손 시 상위 BGP 세션 동반 단절"),
        ]

        for s, t, rel, desc in critical_cross_links:
            if self.graph.has_node(s) and self.graph.has_node(t) and not self.graph.has_edge(s, t):
                self.graph.add_edge(s, t, relationship=rel, description=desc)
                added_causal_links += 1

        logger.info(
            f"Canonicalization complete: merged {merged_nodes_count} duplicate command nodes, "
            f"redirected {redirected_edges_count} edges, added {added_causal_links} cross-domain causal links."
        )

        if save:
            self.save_to_files()

        return {
            "merged_nodes": merged_nodes_count,
            "redirected_edges": redirected_edges_count,
            "added_causal_links": added_causal_links,
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges()
        }

    def _load_from_json(self, json_path: str) -> None:
        """ArangoDB 호환 causal_graph.json 파일에서 노드와 엣지를 로드합니다."""
        self.graph.clear()
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for n in data.get("nodes", []):
                nid = n.get("id") or n.get("_key")
                self.graph.add_node(
                    nid,
                    label=n.get("label", nid),
                    type=n.get("type", "Symptom"),
                    description=n.get("description", ""),
                    details=n.get("details", {})
                )

            for e in data.get("edges", []):
                src = e.get("source") or (e.get("_from", "").split("/")[-1])
                tgt = e.get("target") or (e.get("_to", "").split("/")[-1])
                self.graph.add_edge(
                    src,
                    tgt,
                    relationship=e.get("relationship", "leads_to"),
                    description=e.get("description", "")
                )

            logger.info(f"UniversalGraphEngine loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges from {json_path}")
        except Exception as e:
            logger.error(f"Error loading graph from JSON ({e}). Falling back to Cypher parser.", exc_info=True)
            if Path(self.cypher_file_path).exists():
                self._load_from_cypher(self.cypher_file_path)

    def _load_from_cypher(self, cypher_path: str) -> None:
        """Neo4j 호환 causal_graph.cypher 파일에서 정규식 파서로 노드와 엣지를 로드합니다."""
        self.graph.clear()
        with open(cypher_path, "r", encoding="utf-8") as f:
            text = f.read()

        node_pattern = re.compile(r"CREATE \(:CausalNode \{id: '([^']+)', label: '([^']+)', type: '([^']+)', description: '([^']*)', details: '(.*)'\}\);")
        rel_pattern = re.compile(r"MATCH \(s:CausalNode \{id: '([^']+)'\}\), \(t:CausalNode \{id: '([^']+)'\}\) CREATE \(s\)-\[:Rel \{relationship: '([^']*)', description: '([^']*)'\}\]->\(t\);")

        for line in text.splitlines():
            line = line.strip()
            m_node = node_pattern.match(line)
            if m_node:
                nid, label, ntype, desc, details_str = m_node.groups()
                try:
                    details = json.loads(details_str.replace("\\'", "'"))
                except Exception:
                    details = {}
                self.graph.add_node(nid, label=label, type=ntype, description=desc, details=details)

            m_rel = rel_pattern.match(line)
            if m_rel:
                src, tgt, rel, desc = m_rel.groups()
                self.graph.add_edge(src, tgt, relationship=rel or "leads_to", description=desc)

        logger.info(f"UniversalGraphEngine loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges from Cypher.")

    def save_to_files(self) -> None:
        """현재 그래프 상태를 causal_graph.json(ArangoDB) 및 causal_graph.cypher(Neo4j) 파일에 모두 영구 저장합니다."""
        nodes = []
        for nid, attrs in self.graph.nodes(data=True):
            nodes.append({
                "_key": nid,
                "id": nid,
                "label": attrs.get("label", nid),
                "type": attrs.get("type", "Symptom"),
                "description": attrs.get("description", ""),
                "details": attrs.get("details", {})
            })

        edges = []
        for src, tgt, attrs in self.graph.edges(data=True):
            edges.append({
                "_from": f"CausalNode/{src}",
                "_to": f"CausalNode/{tgt}",
                "source": src,
                "target": tgt,
                "relationship": attrs.get("relationship", "leads_to"),
                "description": attrs.get("description", "")
            })

        # 1. ArangoDB 호환 JSON 저장
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump({
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "format": "ArangoDB & Neo4j Multi-Model Causal Graph Seed",
                    "nodes_count": len(nodes),
                    "edges_count": len(edges)
                }
            }, f, ensure_ascii=False, indent=2)

        # 2. Neo4j 호환 Cypher 파일 저장
        cypher_lines = [
            "// =====================================================================",
            "// Cisco IOS-XE Causal GraphDB - openCypher Definition",
            "// Standard Neo4j & ArangoDB Graph Seed File",
            "// =====================================================================\n",
            "CREATE NODE TABLE IF NOT EXISTS CausalNode (id STRING, label STRING, type STRING, description STRING, details STRING, PRIMARY KEY (id));",
            "CREATE REL TABLE IF NOT EXISTS Rel (FROM CausalNode TO CausalNode, relationship STRING, description STRING);\n"
        ]
        for n in nodes:
            nid = n["id"].replace("'", "\\'")
            label = n["label"].replace("'", "\\'")
            ntype = n["type"].replace("'", "\\'")
            desc = n["description"].replace("'", "\\'")
            details_str = json.dumps(n["details"], ensure_ascii=False).replace("'", "\\'")
            cypher_lines.append(f"CREATE (:CausalNode {{id: '{nid}', label: '{label}', type: '{ntype}', description: '{desc}', details: '{details_str}'}});")

        cypher_lines.append("\n// Relationships")
        for e in edges:
            src = e["source"].replace("'", "\\'")
            tgt = e["target"].replace("'", "\\'")
            rel = e["relationship"].replace("'", "\\'")
            desc = e["description"].replace("'", "\\'")
            cypher_lines.append(f"MATCH (s:CausalNode {{id: '{src}'}}), (t:CausalNode {{id: '{tgt}'}}) CREATE (s)-[:Rel {{relationship: '{rel}', description: '{desc}'}}]->(t);")

        with open(self.cypher_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cypher_lines) + "\n")

    def query_cypher(self, cypher_query: str) -> List[Dict[str, Any]]:
        """openCypher 쿼리를 파싱하여 NetworkX 그래프 상에서 결과를 시뮬레이션 반환합니다."""
        q = cypher_query.strip()
        results = []

        # MATCH (n:CausalNode) RETURN ... 쿼리 처리
        if "RETURN" in q.upper():
            limit_m = re.search(r"LIMIT\s+(\d+)", q, re.IGNORECASE)
            limit = int(limit_m.group(1)) if limit_m else 100

            # 특정 노드 조회
            id_m = re.search(r"id:\s*'([^']+)'", q)
            if id_m:
                nid = id_m.group(1)
                if self.graph.has_node(nid):
                    attrs = self.graph.nodes[nid]
                    results.append({
                        "n.id": nid,
                        "n.label": attrs.get("label", nid),
                        "n.type": attrs.get("type", "Symptom"),
                        "n.description": attrs.get("description", "")
                    })
            else:
                for nid, attrs in list(self.graph.nodes(data=True))[:limit]:
                    results.append({
                        "n.id": nid,
                        "n.label": attrs.get("label", nid),
                        "n.type": attrs.get("type", "Symptom"),
                        "n.description": attrs.get("description", "")
                    })

        return results

    def add_node(self, node: NodeModel) -> None:
        ntype = node.type.value if hasattr(node.type, "value") else str(node.type)
        self.graph.add_node(
            node.id,
            label=node.label,
            type=ntype,
            description=node.description or "",
            details=node.details or {}
        )
        self.save_to_files()

    def delete_node(self, node_id: str) -> bool:
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)
            self.save_to_files()
            return True
        return False

    def add_edge(self, edge: EdgeModel) -> None:
        if not self.graph.has_node(edge.source):
            self.graph.add_node(edge.source, label=edge.source, type=NodeType.SYMPTOM.value, description="", details={})
        if not self.graph.has_node(edge.target):
            self.graph.add_node(edge.target, label=edge.target, type=NodeType.ROOT_CAUSE.value, description="", details={})

        self.graph.add_edge(
            edge.source,
            edge.target,
            relationship=edge.relationship or "leads_to",
            description=edge.description or ""
        )
        self.save_to_files()

    def delete_edge(self, source: str, target: str) -> bool:
        if self.graph.has_edge(source, target):
            self.graph.remove_edge(source, target)
            self.save_to_files()
            return True
        return False

    def compute_topology_layout(self, layout_type: str = "force") -> Dict[str, Dict[str, float]]:
        """NetworkX 기반의 대표 토폴로지 레이아웃 좌표를 계산합니다.
        
        1. hierarchical: 인과 흐름 계층 배치 (Symptom -> RootCause -> Verification -> Command)
        2. radial (concentric): 동심원 궤도 배치 (중앙 Symptom -> 외곽 Command)
        3. force: 기본 자유 배치 (fx/fy 미지정)
        """
        positions: Dict[str, Dict[str, float]] = {}

        if layout_type == "hierarchical":
            # 4대 계층 분류
            layer_types = {
                "Symptom": 0,
                "RootCause": 1,
                "Verification": 2,
                "Command": 3
            }
            
            nodes_by_layer: Dict[int, List[str]] = {0: [], 1: [], 2: [], 3: []}
            for nid, attrs in self.graph.nodes(data=True):
                ntype = attrs.get("type", "Symptom")
                layer_idx = layer_types.get(ntype, 0)
                nodes_by_layer[layer_idx].append(nid)

            # X축 계층 컬럼 좌표 (-550, -180, +180, +550)
            x_offsets = {0: -550.0, 1: -180.0, 2: 180.0, 3: 550.0}

            for l_idx, nids in nodes_by_layer.items():
                count = len(nids)
                if count == 0:
                    continue
                # Y축 균등 분산
                total_span = min(count * 26.0, 950.0)
                y_start = -total_span / 2.0
                y_step = total_span / max(count - 1, 1)

                for i, nid in enumerate(nids):
                    y_pos = y_start + i * y_step if count > 1 else 0.0
                    positions[nid] = {
                        "x": x_offsets[l_idx],
                        "y": y_pos,
                        "fx": x_offsets[l_idx],
                        "fy": y_pos
                    }

        elif layout_type == "radial" or layout_type == "concentric":
            # 4대 동심원 궤도 (Rings)
            ring_radii = {
                "Symptom": 90.0,
                "RootCause": 220.0,
                "Verification": 360.0,
                "Command": 500.0
            }
            import math
            nodes_by_ring: Dict[str, List[str]] = {"Symptom": [], "RootCause": [], "Verification": [], "Command": []}
            for nid, attrs in self.graph.nodes(data=True):
                ntype = attrs.get("type", "Symptom")
                if ntype in nodes_by_ring:
                    nodes_by_ring[ntype].append(nid)
                else:
                    nodes_by_ring["Symptom"].append(nid)

            for ntype, nids in nodes_by_ring.items():
                radius = ring_radii[ntype]
                count = len(nids)
                if count == 0:
                    continue
                angle_step = (2 * math.pi) / count
                for i, nid in enumerate(nids):
                    angle = i * angle_step
                    x_pos = radius * math.cos(angle)
                    y_pos = radius * math.sin(angle)
                    positions[nid] = {
                        "x": x_pos,
                        "y": y_pos,
                        "fx": x_pos,
                        "fy": y_pos
                    }

        return positions

    def get_graph_data(self, layout: Optional[str] = None) -> Dict[str, Any]:
        """react-force-graph-2d 호환 JSON 형식 반환 (선택된 토폴로지 레이아웃 좌표 포함)"""
        layout_positions = {}
        if layout in ("hierarchical", "radial", "concentric"):
            layout_positions = self.compute_topology_layout(layout)

        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_dict: Dict[str, Any] = {
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", NodeType.SYMPTOM.value),
                "description": attrs.get("description", ""),
                "details": attrs.get("details", {})
            }
            # 레이아웃 좌표 주입
            if node_id in layout_positions:
                node_dict.update(layout_positions[node_id])

            nodes.append(node_dict)

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
            "links": links,
            "layout": layout or "force",
            "metadata": {
                "nodes_count": len(nodes),
                "edges_count": len(links),
                "components_count": nx.number_connected_components(self.graph.to_undirected())
            }
        }

    def find_causal_paths(self, start_node_id: str) -> List[Dict[str, Any]]:
        """특정 노드에서 도달 가능한 모든 인과 관계 경로 탐색"""
        if not self.graph.has_node(start_node_id):
            return []

        paths = []
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

    def match_symptom(
        self,
        message: str,
        protocol_hint: Optional[str] = None,
        symptom_intent: Optional[str] = None
    ) -> str:
        """1차 LLM의 symptom_intent 및 프로토콜 힌트로부터 GraphDB 증상 노드 ID를 결정 (휴리스틱 점수 계산 코드 제거)"""
        # 1. 1차 LLM이 추출한 증상 의도가 그래프에 존재하는 경우 즉시 바인딩
        if symptom_intent and self.graph.has_node(symptom_intent):
            return symptom_intent

        msg_lower = message.lower()

        # 2. 프로토콜 기반 명확한 매핑
        p = (protocol_hint or "").lower()
        if "ospf" in p or "ospf" in msg_lower:
            if "exstart" in msg_lower:
                return "symptom_ospf_exstart"
            return "symptom_ospf_down"
        elif "isis" in p or "is-is" in p or "isis" in msg_lower:
            return "symptom_isis_underlay_down"
        elif "bgp" in p or "bgp" in msg_lower:
            if "active" in msg_lower:
                return "symptom_bgp_active"
            elif "flap" in msg_lower or "reset" in msg_lower:
                return "symptom_bgp_flapping"
            return "symptom_bgp_down"
        elif "acl" in p or "drop" in msg_lower or "드롭" in msg_lower or "차단" in msg_lower:
            return "symptom_packet_drop"

        return "symptom_ospf_down"

    def get_diagnostic_workflow(self, symptom_id: str) -> Dict[str, Any]:
        """GraphDB의 인과 경로를 순회하여 OSI 7 계층 순서로 정렬된 검증 CLI 및 복구 방안을 도출"""
        if not self.graph.has_node(symptom_id):
            symptom_id = "symptom_bgp_down"

        symptom_attrs = self.graph.nodes[symptom_id]
        causal_paths = self.find_causal_paths(symptom_id)

        root_causes = []
        verifications = []
        verification_commands = []
        remediation_actions = []

        seen_nodes = set()
        for p_info in causal_paths:
            for step in p_info["steps"]:
                nid = step["id"]
                if nid in seen_nodes:
                    continue
                seen_nodes.add(nid)

                attrs = self.graph.nodes[nid]
                ntype = attrs.get("type")
                entry = {
                    "id": nid,
                    "label": attrs.get("label", nid),
                    "type": ntype,
                    "description": attrs.get("description", ""),
                    "details": attrs.get("details", {})
                }

                if ntype in (NodeType.ROOT_CAUSE.value, "RootCause"):
                    root_causes.append(entry)
                elif ntype in (NodeType.VERIFICATION.value, "Verification"):
                    verifications.append(entry)
                elif ntype in (NodeType.COMMAND.value, "Command"):
                    details = attrs.get("details", {})
                    if details.get("type") == "Remediation":
                        remediation_actions.append(entry)
                    else:
                        cmd_str = details.get("command") or attrs.get("label")
                        entry["command"] = cmd_str
                        verification_commands.append(entry)

        # 중복 명령어 제거
        seen_cmds = set()
        unique_cmds = []
        for c in verification_commands:
            c_str = c.get("command") or c.get("label")
            if c_str not in seen_cmds:
                seen_cmds.add(c_str)
                unique_cmds.append(c)

        # OSI 7 계층 Bottom-Up 우선순위 정렬
        def osi_layer_priority(cmd_entry: Dict[str, Any]) -> int:
            cmd = (cmd_entry.get("command") or "").lower()
            lbl = (cmd_entry.get("label") or "").lower()
            if "brief" in cmd or "interfaces" in cmd or "duplex" in lbl or "mtu" in lbl:
                return 10  # L1/L2
            if "show ip interface" in cmd or "access-list" in cmd or "policy" in cmd or "route-map" in cmd or "acl" in lbl or "pbr" in lbl:
                return 20  # L3 보안 및 PBR
            if "show ip route" in cmd or "ospf" in cmd or "isis" in cmd or "static" in cmd or "ping" in cmd:
                return 30  # L3 언더레이/라우팅
            if "tcp" in cmd or "port" in cmd or "179" in lbl:
                return 40  # L4 전송
            return 50      # L7 BGP 프로토콜

        unique_cmds.sort(key=osi_layer_priority)

        return {
            "symptom": {
                "id": symptom_id,
                "label": symptom_attrs.get("label", symptom_id),
                "description": symptom_attrs.get("description", "")
            },
            "root_causes": root_causes,
            "verifications": verifications,
            "verification_commands": unique_cmds,
            "remediation_actions": remediation_actions,
            "causal_paths": causal_paths
        }


# 전역 인스턴스 (앱 전체에서 공유)
graph_engine = UniversalCausalGraphEngine()
CausalGraphEngine = UniversalCausalGraphEngine  # 이전 클래스명 호환성 보장
