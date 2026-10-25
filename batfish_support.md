# Batfish 지원 기능 및 분석 API 완전 명세서 (`batfish_support.md`)

> **개요:**  
> 본 문서는 Net-AIOps 시스템에서 네트워크 설정의 정형 검증(Formal Verification) 및 인과 추론에 활용 가능한 **Batfish의 모든 분석 함수(총 78개 Question API)와 역할, 세부 파라미터, 반환 데이터 및 AIOps 활용 방안**을 단 하나도 빠짐없이 완벽하게 정리한 공식 기술 명세서입니다.
> 
> - **분석 엔진:** Batfish Formal Network Verification Engine (`batfish/allinone:latest`)
> - **Python 클라이언트:** `pybatfish` (Session: `bf.q.<question>()`)
> - **총 지원 함수 수:** **78개 (100% 전수 수록)**

---

## 📌 대분류 목차

1. **[1. BGP 프로토콜 및 세션 정형 분석 (BGP Analysis)](#1-bgp)**
2. **[2. OSPF / IS-IS / EIGRP 라우팅 정형 분석 (IGP Analysis)](#2-ospf)**
3. **[3. 보안 ACL, 방화벽 및 패킷 필터링 검증 (Security & ACL)](#3-보안)**
4. **[4. 데이터 평면, Traceroute 및 포워딩 분석 (Data Plane & Forwarding)](#4-데이터)**
5. **[5. 라우팅 테이블 및 경로 전파 분석 (RIB / FIB Analysis)](#5-라우팅)**
6. **[6. 인터페이스, L1/L2 토폴로지 및 MTU 분석 (Interface & Topology)](#6-인터페이스,)**
7. **[7. 설정 구문, 미인식 라인 및 결함 참조 분석 (Configuration & Syntax)](#7-설정)**
8. **[8. 라우팅 정책 및 Route-Map 시뮬레이션 (Route Policies)](#8-라우팅)**
9. **[9. 인프라 이중화 및 터널 서비스 (FHRP, IPsec, VXLAN, Management)](#9-인프라)**
10. **[10. Batfish 시스템 메타데이터 및 명세자 (System & Specifiers)](#10-batfish)**
11. **[11. Batfish 78개 Question API ↔ Cisco IOS-XE 실측 CLI 1:1 대응 완전 명세표 (Dual-Engine Mapping)](#11-batfish-78개-question-api--cisco-ios-xe-실측-cli-11-대응-완전-명세표-dual-engine-mapping)**

---

## 1. BGP 프로토콜 및 세션 정형 분석 (BGP Analysis)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.bgpEdges()`** | **BGP 피어 인접성(Adjacency) 및 연결 토폴로지 조회** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 네트워크 내 BGP 피어 간 세션 성립 관계를 그래프 엣지로 도출 |
| **`bf.q.bgpPeerConfiguration()`** | **BGP 네이버별 세부 설정(update-source, multihop, timers) 분석** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 피어링 속성 및 next-hop-self 선언 누락 여부 확인 |
| **`bf.q.bgpProcessConfiguration()`** | **BGP 라우팅 프로세스 및 로컬 AS 번호, Router-ID 설정 검증** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** AS 번호 오설정 및 프로세스 비활성화 탐지 |
| **`bf.q.bgpRib()`** | **BGP 라우팅 정보 베이스(RIB) 전체 테이블 조회 및 최적 경로(Best Path) 분석** | `nodes`, `network`, `prefixMatchType` 외 2개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** AS-Path, Local-Pref, MED, Next-Hop 속성 및 비정상 BGP 경로 탐색 |
| **`bf.q.bgpSessionCompatibility()`** | **BGP 피어 간 설정 호환성(AS 번호, IP, 인증, 타이머) 사전 검증** | `nodes`, `remoteNodes`, `status` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 세션 수립 불가 원인을 실측 트래픽 없이 설정만으로 사전 진단 |
| **`bf.q.bgpSessionStatus()`** | **BGP 세션의 동적 FSM 상태(Established, Idle, Not Compatible 등) 분석** | `nodes`, `remoteNodes`, `status` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 네이버 단절, Admin Shutdown, 세션 리셋 근본 원인 도출 |
| **`bf.q.evpnRib()`** | **EVPN 주소 체계(Type-2, Type-5)의 BGP RIB 라우팅 테이블 분석** | `nodes`, `network`, `prefixMatchType` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 데이터센터 오버레이 EVPN/VXLAN 경로 전파 상태 검증 |

## 2. OSPF / IS-IS / EIGRP 라우팅 정형 분석 (IGP Analysis)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.edges()`** | **네트워크 내 프로토콜별(OSPF, BGP, ISIS, Layer 3 등) 인접성 통합 조회** | `edgeType`, `nodes`, `remoteNodes` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 종합적인 토폴로지 연결 상태 및 인접 관계 점검 |
| **`bf.q.ospfAreaConfiguration()`** | **OSPF Area 타입(Backbone, Stub, NSSA) 및 요약/필터링 설정 검증** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** Area 0 불연속 및 NSSA 설정 불일치 탐지 |
| **`bf.q.ospfEdges()`** | **성립된 OSPF 네이버 인접성(Neighbor Adjacency) 링크 분석** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** OSPF 네이버 다운 및 인터페이스 탈락 탐색 |
| **`bf.q.ospfInterfaceConfiguration()`** | **인터페이스별 OSPF Network Type, Cost, Dead Timer, MTU 설정 분석** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** OSPF ExStart 고착(MTU 불일치) 및 타이머 불일치 진단 |
| **`bf.q.ospfProcessConfiguration()`** | **OSPF 프로세스 ID, Router-ID 및 경로 재분배(Redistribution) 설정 검증** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** IGP 미선언 및 재분배 누락 원인 규명 |
| **`bf.q.ospfSessionCompatibility()`** | **OSPF 피어 간 인접 관계 성립 호환성(Area ID, 타이머, 인증) 검증** | `nodes`, `remoteNodes`, `statuses` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 네이버가 맺어지지 않는 설정 불일치 원인을 100% 특정 |
| **`bf.q.isisEdges()`** | **IS-IS Level-1 및 Level-2 인접 관계(Adjacency) 및 회선 상태 분석** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** IS-IS 언더레이 세션 단절 및 Circuit-Type 불일치 진단 |
| **`bf.q.eigrpEdges()`** | **EIGRP AS 번호 및 K-Value, 네이버 인접성 검증** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** EIGRP 이웃 관계 성립 결함 탐색 |

## 3. 보안 ACL, 방화벽 및 패킷 필터링 검증 (Security & ACL)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.filterLineReachability()`** | **ACL 및 방화벽 룰 중 이전 룰에 가려진 사장된 라인(Unreachable/Shadowed Rules) 탐지** | `nodes`, `filters`, `ignoreComposites` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 중복되거나 도달 불가능한 불필요 보안 룰 분석 |
| **`bf.q.filterTable()`** | **보안 필터 룰셋 테이블 및 조건부 필터링 서브셋 조회** | `innerQuestion`, `columns`, `filter` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 인터페이스에 바인딩된 보안 필터 목록 검토 |
| **`bf.q.findMatchingFilterLines()`** | **특정 패킷 헤더(IP, 포트, 프로토콜)에 정확히 일치하는 ACL 라인 번호 추적** | `nodes`, `filters`, `headers` 외 2개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** BGP(TCP 179)나 트래픽이 차단된 정확한 ACL 라인 번호 도출 |
| **`bf.q.searchFilters()`** | **방화벽/ACL 필터에서 특정 행위(Permit/Deny)를 유발하는 플로우 공간 역추적** | `nodes`, `filters`, `headers` 외 3개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 어떤 트래픽이 차단되고 있는지 보안 정책 매칭 역검색 |
| **`bf.q.testFilters()`** | **임의의 가상 패킷을 주입하여 ACL의 처리 동작(Permit/Deny) 시뮬레이션** | `nodes`, `filters`, `headers` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 실제 패킷 전송 없이 ACL 차단 여부를 0.001초 만에 테스트 |
| **`bf.q.compareFilters()`** | **두 스냅샷(설정 변경 전후) 간 ACL 동작 차이 및 차단/허용 룰셋 변경 분석** | `nodes`, `filters`, `ignoreComposites` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 보안 정책 변경으로 인한 예기치 않은 통신 장애 사전 탐지 |

## 4. 데이터 평면, Traceroute 및 포워딩 분석 (Data Plane & Forwarding)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.traceroute()`** | **지정된 출발지-목적지 간의 패킷 전달 경로(Hop-by-Hop) 및 중간 드롭 지점(Drop Reason) 정형 추적** | `startLocation`, `headers`, `maxTraces` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 중간 경유 라우터의 ACL 차단, No Route, Null0 폐기 지점 특정 |
| **`bf.q.bidirectionalTraceroute()`** | **출발지와 목적지 간의 왕복(Forward/Reverse) 패킷 전달 경로 동시 추적** | `startLocation`, `headers`, `maxTraces` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 비대칭 라우팅(Asymmetric Routing) 및 복귀 경로 단절 분석 |
| **`bf.q.reachability()`** | **네트워크 전체에서 특정 목적지에 도달 가능한 모든 유효 트래픽 플로우 검색** | `pathConstraints`, `headers`, `actions` 외 3개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 엔드-투-엔드 통신 가능성 및 고립된 구간 탐색 |
| **`bf.q.bidirectionalReachability()`** | **요청 및 응답이 양방향으로 모두 성공하는 완전한 양방향 통신 플로우 검증** | `pathConstraints`, `headers`, `returnFlowType` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** TCP 3-Way Handshake 수립 가능 여부 정형 증명 |
| **`bf.q.detectLoops()`** | **네트워크 내 포워딩 루프(Forwarding Loop) 및 패킷 무한 순환 구간 탐지** | `maxTraces` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 라우팅 루프로 인한 대역폭 고갈 및 세션 리셋 진단 |
| **`bf.q.multipathConsistency()`** | **전체 네트워크의 다중 경로(Multipath) 도달성 및 일관성 정형 검증** | `pathConstraints`, `headers`, `maxTraces` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 동일 서브넷/플로우에 대한 ECMP 경로 무결성 분석 |
| **`bf.q.loopbackMultipathConsistency()`** | **모든 루프백 IP 간의 다중 경로(Multipath) 도달성 일관성 검증** | `maxTraces` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 언더레이 루프백 간 로드밸런싱 및 백본 일관성 점검 |
| **`bf.q.subnetMultipathConsistency()`** | **모든 서브넷 간의 다중 경로(Multipath) 도달성 일관성 검증** | `maxTraces` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 데이터 서브넷 간 경로 불일치 및 편향 현상 탐색 |
| **`bf.q.differentialReachability()`** | **설정 변경 전후 두 스냅샷 간 도달성 차이(신규 차단/신규 허용) 분석** | `pathConstraints`, `headers`, `actions` 외 3개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 설정 변경으로 인해 끊어진 트래픽 플로우를 정확히 식별 |

## 5. 라우팅 테이블 및 경로 전파 분석 (RIB / FIB Analysis)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.routes()`** | **전체 장비의 메인 라우팅 테이블(RIB) 조회 (Connected, Static, OSPF, BGP 등)** | `nodes`, `network`, `prefixMatchType` 외 3개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 특정 Next-Hop이나 대역의 라우팅 테이블 등록 여부 확인 |
| **`bf.q.lpmRoutes()`** | **특정 목적지 IP에 대해 Longest Prefix Match(LPM)로 최종 선택되는 라우팅 엔트리 분석** | `ip`, `nodes`, `vrfs` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 패킷이 실제로 포워딩될 최적 게이트웨이 및 인터페이스 특정 |
| **`bf.q.prefixTracer()`** | **특정 IP 서브넷 Prefix가 네트워크 전역에 어떻게 전파되고 재분배되는지 추적** | `nodes`, `prefix` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** Route-Map이나 BGP/IGP 전파 과정에서의 Prefix 누락 지점 규명 |

## 6. 인터페이스, L1/L2 토폴로지 및 MTU 분석 (Interface & Topology)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.interfaceProperties()`** | **물리/가상 인터페이스의 IP, VRF, Bandwidth, MTU, 활성화 상태(shutdown) 종합 분석** | `nodes`, `interfaces`, `properties` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 인터페이스 Admin Down, 잘못된 서브넷 마스크 설정 탐지 |
| **`bf.q.interfaceMtu()`** | **네트워크 내 인터페이스 MTU 값 검증 및 대향 장비 간 MTU 불일치 탐지** | `interfaces`, `mtuBytes`, `nodes` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** MTU 불일치로 인한 대용량 패킷 폐기 및 OSPF/BGP 단절 진단 |
| **`bf.q.ipOwners()`** | **IP 주소가 어느 장비의 어느 인터페이스에 할당되어 있는지 전역 조회** | `ips`, `duplicatesOnly` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 동일 서브넷 내 중복 IP(IP Conflict/Duplication) 충돌 감지 |
| **`bf.q.layer1Edges()`** | **Layer 1 물리적 케이블 연결 토폴로지 링크 조회** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 물리 결선 구성 및 포트 매핑 확인 |
| **`bf.q.layer3Edges()`** | **Layer 3 논리적 IP 라우팅 링크 토폴로지 조회** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 라우터 간 서브넷 연결 및 IP 인접성 검증 |
| **`bf.q.userProvidedLayer1Edges()`** | **사용자가 입력한 L1 물리 연결 정보와 설정 간의 일치성 검증** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 케이블 오결선 및 포트 불일치 확인 |
| **`bf.q.switchedVlanProperties()`** | **스위치 내 VLAN 속성 및 허용 VLAN(Allowed VLAN) 리스트 분석** | `nodes`, `interfaces`, `vlans` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 트렁크 포트에서 특정 VLAN 누락 여부 확인 |

## 7. 설정 구문, 미인식 라인 및 결함 참조 분석 (Configuration & Syntax)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.initIssues()`** | **스냅샷 초기화 및 파싱 과정에서 발생한 구문 오류 및 문제점 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 설정 파일 로드 시의 치명적 결함 및 누락 진단 |
| **`bf.q.parseWarning()`** | **벤더 비호환 구문이나 Batfish가 파싱하지 못한 미지원 CLI 라인 경고 분석** | `aggregateDuplicates` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 인식되지 않은 특수 명령어 및 설정 누락 파악 |
| **`bf.q.fileParseStatus()`** | **각 장비별 설정 파일의 파싱 성공률 및 상태(PASSED, FAILED) 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 스냅샷 내 장비 설정의 정합성 확인 |
| **`bf.q.nodeProperties()`** | **장비 노드 속성(호스트명, 벤더, DNS, 리졸버, 도메인) 분석** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 장비 기본 시스템 파라미터 점검 |
| **`bf.q.definedStructures()`** | **설정 내 정의된 모든 구조체(ACL, Route-map, Prefix-list, VRF 등) 목록 추출** | `filename`, `nodes`, `names` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 네트워크 객체 정의 현황 파악 |
| **`bf.q.referencedStructures()`** | **설정에서 참조 중인 벤더별 구조체 목록 및 사용 위치 추적** | `nodes`, `names`, `types` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 정책에서 사용 중인 객체 추적 |
| **`bf.q.undefinedReferences()`** | **정의되지 않은 Route-map, ACL, Prefix-list를 참조하는 설정 결함(Dangling Reference) 탐지** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 존재하지 않는 ACL을 인터페이스에 걸어 트래픽이 전면 차단되는 장애 예방 |
| **`bf.q.unusedStructures()`** | **정의는 되어 있으나 어떤 인터페이스나 라우팅에도 적용되지 않은 미사용 설정(Unused Object) 탐지** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 설정 다이어트 및 불필요 정책 정리 |

## 8. 라우팅 정책 및 Route-Map 시뮬레이션 (Route Policies)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.searchRoutePolicies()`** | **Route-Map 및 라우팅 정책이 특정 경로를 어떻게 처리(Permit/Deny/Set)하는지 역추적** | `nodes`, `policies`, `inputConstraints` 외 4개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** BGP/OSPF 경로 필터링 정책의 동작 검증 |
| **`bf.q.testRoutePolicies()`** | **가상 라우트 알림(Route Announcement)을 Route-Map에 투입하여 속성 변경 시뮬레이션** | `nodes`, `policies`, `inputRoutes` 외 2개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** Next-Hop 변경, Local-Pref 변경, Community 부착 결과 사전 검증 |
| **`bf.q.compareRoutePolicies()`** | **설정 변경 전후 Route-Map 정책의 변경 사항 및 동작 차이 분석** | `policy`, `referencePolicy`, `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 라우팅 정책 수정으로 인한 예기치 않은 경로 누락 방지 |
| **`bf.q.comparePeerGroupPolicies()`** | **피어 그룹 간 BGP 라우팅 정책 차이점 비교 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** BGP Peer-Group 간 정책 불일치 탐지 |

## 9. 인프라 이중화 및 터널 서비스 (FHRP, IPsec, VXLAN, Management)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.hsrpProperties()`** | **Cisco HSRP 이중화 그룹, Priority, 가상 IP 설정 분석** | `nodes`, `interfaces`, `virtualAddresses` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** HSRP 액티브/스탠바이 선출 불일치 및 이중 액티브 방지 |
| **`bf.q.vrrpProperties()`** | **표준 VRRP 게이트웨이 이중화 그룹 및 가상 라우터 상태 분석** | `nodes`, `interfaces`, `virtualAddresses` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** VRRP Priority 및 가상 IP 주소 일치성 점검 |
| **`bf.q.mlagProperties()`** | **MLAG / vPC 멀티섀시 링크 애그리게이션 설정 분석** | `nodes`, `mlagIds` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 스위치 간 피어링크 및 도메인 ID 불일치 탐색 |
| **`bf.q.ipsecEdges()`** | **IPsec VPN 터널 연결성 및 피어 인접성 분석** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 사이트 간 VPN 터널 단절 및 터널 인터페이스 상태 확인 |
| **`bf.q.ipsecSessionStatus()`** | **설정된 IPsec 세션의 협상 상태(Negotiated, Missing, Incompatible) 분석** | `nodes`, `remoteNodes`, `status` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** IKE Phase 1/2 불일치 및 PSK 암호 불일치 진단 |
| **`bf.q.vxlanEdges()`** | **VXLAN 터널 엔드포인트(VTEP) 간 오버레이 엣지 연결 분석** | `nodes`, `remoteNodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 데이터센터 오버레이 터널 수립 상태 검증 |
| **`bf.q.vxlanVniProperties()`** | **VXLAN VNI 매핑 및 멀티캐스트 그룹/바인딩 속성 분석** | `nodes`, `properties` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** VNI 번호 불일치 및 캡슐화 결함 탐색 |
| **`bf.q.evpnL3VniProperties()`** | **EVPN Layer 3 VNI 및 테넌트 VRF 매핑 속성 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 테넌트 간 L3 분리 및 라우팅 인터페이스 검증 |
| **`bf.q.snmpCommunityClients()`** | **특정 SNMP 커뮤니티가 지정된 클라이언트 IP의 접근을 허용하는지 검증** | `community`, `clients`, `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** NMS IP 차단 및 모니터링 단절 확인 |
| **`bf.q.aaaAuthenticationLogin()`** | **인증 없는 가상 터미널(VTY 라인) 보안 취약점 점검** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** Telnet/SSH 로그인 시 비밀번호 없는 보안 취약점 탐지 |
| **`bf.q.a10VirtualServerConfiguration()`** | **A10 로드밸런서의 Virtual Server 설정 분석** | `nodes`, `virtualServerIps` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** ADC VIP 바인딩 및 서비스 포트 점검 |
| **`bf.q.f5BigipVipConfiguration()`** | **F5 BIG-IP LTM Virtual Server 및 풀 바인딩 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** F5 부하 분산 설정 정합성 확인 |

## 10. Batfish 시스템 메타데이터 및 명세자 (System & Specifiers)

| 함수명 (`bf.q.<function>`) | 역할 및 정형 분석 내용 | 주요 파라미터 | 반환 데이터 및 Net-AIOps 활용 방안 |
| :--- | :--- | :--- | :--- |
| **`bf.q.list()`** | **Batfish 서비스에서 현재 사용 가능한 모든 Question API 목록 조회** | `tags` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 지원 쿼리 메타데이터 열람 |
| **`bf.q.list_tags()`** | **사용 가능한 분석 질문들의 카테고리 태그 목록 조회** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 분석 주제별 태그 인덱싱 |
| **`bf.q.load()`** | **로컬 디렉토리 또는 원격 서비스로부터 사용자 정의 분석 질문 로드** | `directory` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 커스텀 정형 질문 확장 |
| **`bf.q.namedStructures()`** | **네트워크 내 명명된 모든 설정 구조체 상세 조회** | `nodes`, `structureTypes`, `structureNames` 외 2개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 구조체 세부 속성 덤프 |
| **`bf.q.resolveFilterSpecifier()`** | **필터 명세자(Filter Specifier) 문법에 매칭되는 필터 목록 반환** | `filters`, `grammarVersion`, `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 정규식 기반 ACL 타겟팅 |
| **`bf.q.resolveInterfaceSpecifier()`** | **인터페이스 명세자 문법에 매칭되는 인터페이스 목록 반환** | `interfaces`, `grammarVersion`, `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 정규식 기반 포트 타겟팅 |
| **`bf.q.resolveIpSpecifier()`** | **IP 명세자 문법에 매칭되는 IP 주소 공간 반환** | `ips`, `grammarVersion` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** IP 서브넷 타겟팅 |
| **`bf.q.resolveIpsOfLocationSpecifier()`** | **특정 위치(Location)에 자동 할당된 IP 주소 반환** | `locations`, `grammarVersion` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 토폴로지 위치별 IP 매핑 |
| **`bf.q.resolveLocationSpecifier()`** | **위치 명세자에 매칭되는 인터페이스 및 노드 반환** | `locations`, `grammarVersion` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 정규식 기반 네트워크 위치 지정 |
| **`bf.q.resolveNodeSpecifier()`** | **노드 명세자에 매칭되는 장비 호스트명 목록 반환** | `nodes`, `grammarVersion` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 정규식 기반 장비 그룹 타겟팅 |
| **`bf.q.transferBDDValidation()`** | **심볼릭 BDD 엔진과 실제 라우팅 시뮬레이션 간의 수학적 동등성 검증** | `nodes`, `policies`, `retainAllPaths` 외 1개 | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** Batfish 자체 정형 엔진 검증 |
| **`bf.q.viConversionStatus()`** | **벤더 중립 모델(Vendor-Independent Model)로의 변환 상태 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 시스코/주니퍼/아리스타 모델 파싱 상태 점검 |
| **`bf.q.viConversionWarning()`** | **벤더 중립 모델 변환 시 발생한 경고 메시지 분석** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 모델 변환 시 누락된 세부 속성 확인 |
| **`bf.q.viModel()`** | **네트워크 내 노드 및 엣지의 벤더 중립 설정 속성 덤프** | `nodes` | **반환:** `TableAnswerElement` (Pandas DataFrame)<br>**활용:** 전체 네트워크 표준 모델 데이터 추출 |

---
## 📊 전체 함수 알파벳 전수 색인 (Total 78 Functions)

| No. | 함수명 (1열) | No. | 함수명 (2열) | No. | 함수명 (3열) |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | `bf.q.a10VirtualServerConfiguration()` | 27 | `bf.q.initIssues()` | 53 | `bf.q.referencedStructures()` |
| 2 | `bf.q.aaaAuthenticationLogin()` | 28 | `bf.q.interfaceMtu()` | 54 | `bf.q.resolveFilterSpecifier()` |
| 3 | `bf.q.bgpEdges()` | 29 | `bf.q.interfaceProperties()` | 55 | `bf.q.resolveInterfaceSpecifier()` |
| 4 | `bf.q.bgpPeerConfiguration()` | 30 | `bf.q.ipOwners()` | 56 | `bf.q.resolveIpSpecifier()` |
| 5 | `bf.q.bgpProcessConfiguration()` | 31 | `bf.q.ipsecEdges()` | 57 | `bf.q.resolveIpsOfLocationSpecifier()` |
| 6 | `bf.q.bgpRib()` | 32 | `bf.q.ipsecSessionStatus()` | 58 | `bf.q.resolveLocationSpecifier()` |
| 7 | `bf.q.bgpSessionCompatibility()` | 33 | `bf.q.isisEdges()` | 59 | `bf.q.resolveNodeSpecifier()` |
| 8 | `bf.q.bgpSessionStatus()` | 34 | `bf.q.layer1Edges()` | 60 | `bf.q.routes()` |
| 9 | `bf.q.bidirectionalReachability()` | 35 | `bf.q.layer3Edges()` | 61 | `bf.q.searchFilters()` |
| 10 | `bf.q.bidirectionalTraceroute()` | 36 | `bf.q.list()` | 62 | `bf.q.searchRoutePolicies()` |
| 11 | `bf.q.compareFilters()` | 37 | `bf.q.list_tags()` | 63 | `bf.q.snmpCommunityClients()` |
| 12 | `bf.q.comparePeerGroupPolicies()` | 38 | `bf.q.load()` | 64 | `bf.q.subnetMultipathConsistency()` |
| 13 | `bf.q.compareRoutePolicies()` | 39 | `bf.q.loopbackMultipathConsistency()` | 65 | `bf.q.switchedVlanProperties()` |
| 14 | `bf.q.definedStructures()` | 40 | `bf.q.lpmRoutes()` | 66 | `bf.q.testFilters()` |
| 15 | `bf.q.detectLoops()` | 41 | `bf.q.mlagProperties()` | 67 | `bf.q.testRoutePolicies()` |
| 16 | `bf.q.differentialReachability()` | 42 | `bf.q.multipathConsistency()` | 68 | `bf.q.traceroute()` |
| 17 | `bf.q.edges()` | 43 | `bf.q.namedStructures()` | 69 | `bf.q.transferBDDValidation()` |
| 18 | `bf.q.eigrpEdges()` | 44 | `bf.q.nodeProperties()` | 70 | `bf.q.undefinedReferences()` |
| 19 | `bf.q.evpnL3VniProperties()` | 45 | `bf.q.ospfAreaConfiguration()` | 71 | `bf.q.unusedStructures()` |
| 20 | `bf.q.evpnRib()` | 46 | `bf.q.ospfEdges()` | 72 | `bf.q.userProvidedLayer1Edges()` |
| 21 | `bf.q.f5BigipVipConfiguration()` | 47 | `bf.q.ospfInterfaceConfiguration()` | 73 | `bf.q.viConversionStatus()` |
| 22 | `bf.q.fileParseStatus()` | 48 | `bf.q.ospfProcessConfiguration()` | 74 | `bf.q.viConversionWarning()` |
| 23 | `bf.q.filterLineReachability()` | 49 | `bf.q.ospfSessionCompatibility()` | 75 | `bf.q.viModel()` |
| 24 | `bf.q.filterTable()` | 50 | `bf.q.parseWarning()` | 76 | `bf.q.vrrpProperties()` |
| 25 | `bf.q.findMatchingFilterLines()` | 51 | `bf.q.prefixTracer()` | 77 | `bf.q.vxlanEdges()` |
| 26 | `bf.q.hsrpProperties()` | 52 | `bf.q.reachability()` | 78 | `bf.q.vxlanVniProperties()` |

---

### 💡 Net-AIOps 시스템과의 연동 아키텍처 요약
1. **실시간 설정 스냅샷 생성:** `IOSXEMCPTool`이 Cisco IOS-XE 장비에서 `show running-config`를 실시간 수집 ➔ `sanitize_config()`로 정제 ➔ `configs/<hostname>.cfg` 스냅샷 패키징.
2. **Batfish 결정론적 검증:** 상기 78개 질문 함수 중 증상에 매핑된 핵심 함수(`bgpSessionStatus`, `filterLineReachability`, `traceroute`, `routes` 등)를 호출하여 팩트 확정.
3. **GraphDB 인과 매핑 & Pruning:** Batfish가 확인한 위반 사항을 GraphDB 노드(`rc_interface_acl_blocked`, `rc_pbr_policy_override` 등)와 매칭하고, 불일치하는 후보 원인들을 100% 제거(가지치기).
4. **초경량 LLM 리포트:** 최종 확정된 단 1개의 근본 원인과 Batfish 증거만 LLM에 전달하여 환각 없는 2초 내 진단 리포트 스트리밍.

---

## 11. Batfish 78개 Question API ↔ Cisco IOS-XE 실측 CLI 1:1 대응 완전 명세표 (Dual-Engine Mapping)

> **듀얼 엔진(Dual-Engine) 교차 검증 체계:**  
> 본 명세는 Net-AIOps GraphDB에 영구 등록된 **Batfish 78개 정형 검증 API(`batfish_question`)**와 실제 Cisco IOS-XE 라우터 현장에서 실행되는 **대응 CLI 명령어(`cli_command`)** 간의 1:1 쌍(Pair) 전수 매핑 테이블입니다.  
> Batfish 시뮬레이션의 수학적 정형 사실과 라우터 실측 텔레메트리 데이터를 상호 교차 대조하여 오탐을 0%로 줄이고, LLM이 계층별 인과 추론을 완벽하게 수행할 수 있는 팩트 번들을 제공합니다.

| No. | Batfish Question API (`bf.q.*`) | 대응 Cisco IOS-XE CLI 명령어 | 검증 계층 (OSI Layer) | Batfish 반환 핵심 컬럼 | 정형 검증 내용 및 교차 점검 목적 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | `bf.q.a10VirtualServerConfiguration()` | `show ip virtual-reassembly` | L4-L7 Application | `Node, Virtual_Server_Name, IP, Port, Type` | A10 ADC Virtual Server 및 서비스 포트 바인딩 정합성 검증 |
| **2** | `bf.q.aaaAuthenticationLogin()` | `show running-config \| section line vty` | Device Security | `Node, Line_Names` | 콘솔/VTY 원격 접속 라인의 인증 방식 및 무암호 보안 취약점 점검 |
| **3** | `bf.q.bgpEdges()` | `show ip bgp summary` | Layer 7 (BGP Peering) | `Node, IP, Remote_Node, Remote_IP` | BGP 피어 간 세션 수립 엣지 및 토폴로지 연결 상태 검증 |
| **4** | `bf.q.bgpPeerConfiguration()` | `show ip bgp neighbors` | Layer 7 (BGP Peering) | `Node, Remote_AS, Remote_IP, Local_IP, Peer_Group` | BGP 피어별 AS, 인터페이스, update-source, next-hop-self 설정 검증 |
| **5** | `bf.q.bgpProcessConfiguration()` | `show running-config \| section router bgp` | Layer 7 (BGP Peering) | `Node, Router_ID, Confederation_ID, Multipath_EBGP` | BGP 프로세스 전역 설정, Router-ID 및 다중 경로 활성화 검증 |
| **6** | `bf.q.bgpRib()` | `show ip bgp` | Layer 7 (BGP Peering) | `Node, Network, Status, Next_Hop, AS_Path, Local_Pref` | BGP 라우팅 테이블(RIB) 내 최적 경로(Best Path) 및 Next-Hop 정합성 검증 |
| **7** | `bf.q.bgpSessionCompatibility()` | `show ip bgp neighbors <peer_ip>` | Layer 7 (BGP Peering) | `Node, Local_IP, Remote_IP, Configured_Status` | 양단 장비 간 BGP 파라미터(AS 번호, IP, MD5 인증) 정합성 사전 검증 |
| **8** | `bf.q.bgpSessionStatus()` | `show ip bgp summary` | Layer 7 (BGP Peering) | `Node, Local_IP, Remote_IP, Established_Status` | 실시간 BGP 피어링 FSM 세션 상태(Established, Idle, Active) 검증 |
| **9** | `bf.q.bidirectionalReachability()` | `ping <dst> source <src> repeat 5` | Layer 4 (Transport) | `Flow, Traces, Return_Flow, Return_Traces` | 양방향 세션 수립을 위한 왕복 트래픽 도달 가능성 정형 검증 |
| **10** | `bf.q.bidirectionalTraceroute()` | `traceroute <dst> source <src>` | Layer 4 (Transport) | `Forward_Flow, Forward_Traces, Reverse_Traces` | 왕복 패킷(SYN/SYN-ACK)의 양방향 홉별 전달 및 ACL 차단 위치 검증 |
| **11** | `bf.q.compareFilters()` | `show archive config differences` | Layer 3 (Security Filter) | `Node, Filter_Name, Difference` | 설정 변경 전/후 ACL 룰의 허용/차단 패킷 범위 변화 차분 분석 |
| **12** | `bf.q.comparePeerGroupPolicies()` | `show ip bgp template peer-policy` | Layer 7 (BGP Peering) | `Node, Peer_Group, Difference` | BGP 피어 그룹 및 정책 템플릿 변경 전/후 정합성 차분 비교 |
| **13** | `bf.q.compareRoutePolicies()` | `show archive config differences` | Layer 3 (Policy Routing) | `Node, Policy_Name, Difference` | 라우팅 정책(Route-Map) 변경 전/후의 허용/거부/변조 결과 차분 분석 |
| **14** | `bf.q.definedStructures()` | `show running-config \| section <type>` | Config Hygiene | `Structure_Type, Structure_Name, Source_Lines` | 설정 내 정의된 모든 명명된 구조체(ACL, VRF, Route-Map) 인벤토리 |
| **15** | `bf.q.detectLoops()` | `traceroute <ip>` | Layer 3 (Underlay Routing) | `Flow, Traces` | 네트워크 포워딩 경로 상의 전달 루프(Forwarding Loop) 수학적 탐지 |
| **16** | `bf.q.differentialReachability()` | `show archive config differences` | Layer 3 (Underlay Routing) | `Flow, Snapshot_Traces, Reference_Traces` | 설정 변경 전/후의 트래픽 도달 가능성 차이(회귀 분석) 정형 검증 |
| **17** | `bf.q.edges()` | `show cdp neighbors detail` | Layer 2 (Data Link) | `Interface, IPs, Remote_Interface, Remote_IPs` | 네트워크 내 모든 프로토콜(L1, L3, BGP, OSPF 등) 인접 엣지 통합 조회 |
| **18** | `bf.q.eigrpEdges()` | `show ip eigrp neighbors` | Layer 3 (Underlay Routing) | `Interface, Remote_Interface` | EIGRP 인접 이웃 엣지 및 K-Value 호환성 검증 |
| **19** | `bf.q.evpnL3VniProperties()` | `show nve vni` | Layer 3 (Overlay) | `Node, VNI, VRF, Route_Target` | EVPN Layer 3 VNI 및 테넌트 VRF 매핑 속성 분석 |
| **20** | `bf.q.evpnRib()` | `show bgp l2vpn evpn` | Layer 7 (BGP Peering) | `Node, Network, Status, Next_Hop, Route_Distinguisher` | EVPN Type-2/Type-5 라우트 BGP RIB 검증 |
| **21** | `bf.q.f5BigipVipConfiguration()` | `show running-config \| section vrf` | L4-L7 Application | `Node, Virtual_Server_Name, IP, Port` | F5 BIG-IP LTM Virtual Server 및 풀 바인딩 분석 |
| **22** | `bf.q.fileParseStatus()` | `show running-config` | Config Hygiene | `File_Name, Status, File_Format, Nodes` | 네트워크 내 각 라우터 설정 파일의 파싱 성공/부분 실패 상태 요약 |
| **23** | `bf.q.filterLineReachability()` | `show ip access-lists` | Layer 3 (Security Filter) | `Node, Filter_Name, Line, Action` | ACL 내에서 앞선 규칙에 가려 절대 실행되지 않는 무효(Shadowed) 라인 검증 |
| **24** | `bf.q.filterTable()` | `show access-lists` | Layer 3 (Security Filter) | `Columns (Dynamic Subsets)` | 정형 질문 결과 테이블을 조건부로 필터링하여 특정 위반 사항 추출 |
| **25** | `bf.q.findMatchingFilterLines()` | `show ip access-lists <name>` | Layer 3 (Security Filter) | `Node, Filter, Line, Line_Index, Action` | 특정 패킷 헤더와 일치하는 구체적인 필터 룰 라인 번호 검색 |
| **26** | `bf.q.hsrpProperties()` | `show standby brief` | Layer 3 (FHRP) | `Interface, Group, Virtual_IP, Priority, Active_Node` | HSRP 그룹 번호, 가상 IP, Priority, Preempt 상태 및 Active/Standby 검증 |
| **27** | `bf.q.initIssues()` | `show logging` | Config Hygiene | `Nodes, Source_Lines, Type, Details, Line_Text` | 설정 로드 시 발생한 구문 파싱 경고 및 미인식 문법 분석 |
| **28** | `bf.q.interfaceMtu()` | `show interfaces \| include MTU` | Layer 2 (Data Link) | `Interface, MTU` | 인터페이스 MTU 크기 및 양단 장비 간 MTU 불일치 여부 검증 |
| **29** | `bf.q.interfaceProperties()` | `show interfaces` | Layer 2 (Data Link) | `Interface, Active, Admin_Up, Speed, Duplex, MTU, VRF` | 인터페이스 상태(Up/Down), Speed, Duplex, VRF, Bandwidth 검증 |
| **30** | `bf.q.ipOwners()` | `show ip interface brief` | Layer 3 (Underlay Routing) | `Node, VRF, Interface, IP, Mask, Active` | 모든 IP 주소의 소유 장비 및 인터페이스, 중복 IP(IP Collision) 검증 |
| **31** | `bf.q.ipsecEdges()` | `show crypto ipsec sa` | Layer 3 (VPN) | `Node, Remote_Node, Tunnel_Interface` | IPsec VPN 터널 엣지 및 피어 연결 관계 검증 |
| **32** | `bf.q.ipsecSessionStatus()` | `show crypto session` | Layer 3 (VPN) | `Node, Remote_Node, Status` | IPsec IKE Phase 1 / Phase 2 보안 세션 수립 상태 검증 |
| **33** | `bf.q.isisEdges()` | `show isis neighbors` | Layer 3 (Underlay Routing) | `Interface, Remote_Interface` | IS-IS 인접 이웃 엣지 및 회선 상태(L1/L2) 검증 |
| **34** | `bf.q.layer1Edges()` | `show cdp neighbors` | Layer 1 (Physical) | `Interface, Remote_Interface` | 물리 계층 1 포트 대 포트 직접 케이블 연결 관계 검증 |
| **35** | `bf.q.layer3Edges()` | `show ip interface brief` | Layer 3 (Underlay Routing) | `Interface, IPs, Remote_Interface, Remote_IPs` | 인터페이스 IP 서브넷 기반 Layer 3 논리적 링크 토폴로지 동적 계산 |
| **36** | `bf.q.list()` | `help` | Batfish System | `Name, Description, Tags` | 현재 Batfish 서비스에서 사용 가능한 전체 정형 분석 질문 API 인벤토리 조회 |
| **37** | `bf.q.list_tags()` | `help` | Batfish System | `Tag, Questions_Count` | 질문 API 분류 카테고리 태그 목록 조회 |
| **38** | `bf.q.load()` | `copy running-config ...` | Batfish System | `Status, Loaded_Questions` | 외부 디렉토리에서 사용자 정의 정형 분석 질문 로드 및 확장 |
| **39** | `bf.q.loopbackMultipathConsistency()` | `show ip cef <loopback_ip>` | Layer 3 (Underlay Routing) | `Flow, Traces` | 루프백 목적지에 대한 다중 경로 포워딩 일관성 검증 |
| **40** | `bf.q.lpmRoutes()` | `show ip route <ip> longer-prefixes` | Layer 3 (Underlay Routing) | `Node, VRF, Ip, Network, Num_Routes` | 특정 목적지 IP에 대한 최장 일치(Longest Prefix Match) 경로 검색 |
| **41** | `bf.q.mlagProperties()` | `show etherchannel summary` | Layer 2 (LAG) | `Node, MLAG_ID, Interface, Peer_Interface` | 멀티섀시 링크 애그리게이션(MLAG / EtherChannel) 상태 검증 |
| **42** | `bf.q.multipathConsistency()` | `show ip cef exact-route <src> <dst>` | Layer 3 (Underlay Routing) | `Flow, Traces` | 동일 목적지에 대한 다중 경로(ECMP) 전달 일관성 및 루프 검증 |
| **43** | `bf.q.namedStructures()` | `show running-config` | Specifier Resolver | `Node, Structure_Type, Structure_Name, Structure_Definition` | 지정된 노드의 특정 명명된 구조체(ACL, Route-Map, VRF 등) 정의 상세 내용 조회 |
| **44** | `bf.q.nodeProperties()` | `show version` | Device Management | `Node, Hostname, Configuration_Format, Interfaces, VRFs` | 장비 호스트명, 벤더 OS 모델, DNS, NTP, 전역 속성 검증 |
| **45** | `bf.q.ospfAreaConfiguration()` | `show ip ospf` | Layer 3 (Underlay Routing) | `Node, VRF, Process_ID, Area, Area_Type, Active_Interfaces` | OSPF Area ID 및 Area 타입(Stub/NSSA) 설정 속성 검증 |
| **46** | `bf.q.ospfEdges()` | `show ip ospf neighbor` | Layer 3 (Underlay Routing) | `Interface, Remote_Interface` | 양단 장비 간 Full 상태 OSPF 인접 엣지 검증 |
| **47** | `bf.q.ospfInterfaceConfiguration()` | `show ip ospf interface` | Layer 3 (Underlay Routing) | `Interface, VRF, Process_ID, OSPF_Cost, OSPF_Hello_Interval` | 인터페이스별 OSPF Cost, Hello/Dead 타이머, Network Type 검증 |
| **48** | `bf.q.ospfProcessConfiguration()` | `show ip ospf` | Layer 3 (Underlay Routing) | `Node, VRF, Process_ID, Router_ID, Areas, Reference_Bandwidth` | OSPF 프로세스 전역 설정 및 Router-ID 검증 |
| **49** | `bf.q.ospfSessionCompatibility()` | `show ip ospf neighbor` | Layer 3 (Underlay Routing) | `Interface, IP, Area, Remote_Interface, Remote_IP, Session_Status` | 양단 장비 간 OSPF 파라미터 정합성 검증 (Router-ID 충돌, Area/MTU 불일치) |
| **50** | `bf.q.parseWarning()` | `show running-config` | Config Hygiene | `Filename, Line, Text, Parser_Context, Comment` | 벤더별 설정 파싱 시 발생한 세부 경고 라인 분석 |
| **51** | `bf.q.prefixTracer()` | `show ip route <prefix>` | Layer 3 (Underlay Routing) | `Node, VRF, Prefix, Route_Count` | 특정 IP Prefix가 어느 노드를 거쳐 학습/광고되었는지 경로 추적 |
| **52** | `bf.q.reachability()` | `ping <dst> source <src>` | Layer 3 (Underlay Routing) | `Flow, Traces, TraceCount` | 모든 유효 패킷 공간에 대한 종단 간(End-to-End) 도달 가능성 정형 검증 |
| **53** | `bf.q.referencedStructures()` | `show running-config` | Config Hygiene | `Structure_Type, Structure_Name, Context, Source_Lines` | 다른 설정에서 참조하고 있는 구조체 목록 검증 |
| **54** | `bf.q.resolveFilterSpecifier()` | `show ip access-lists` | Specifier Resolver | `Node, Filter_Name` | 필터 명세자에 매칭되는 ACL 및 패킷 필터 이름 해석 |
| **55** | `bf.q.resolveInterfaceSpecifier()` | `show ip interface brief` | Specifier Resolver | `Interface` | 인터페이스 명세자에 일치하는 네트워크 포트 목록 해석 |
| **56** | `bf.q.resolveIpSpecifier()` | `show ip route` | Specifier Resolver | `IP_Space` | IP 명세자(CIDR/와일드카드)에 매칭되는 실제 IP 주소 공간 해석 |
| **57** | `bf.q.resolveIpsOfLocationSpecifier()` | `show ip interface brief` | Specifier Resolver | `Locations, IP_Space` | 특정 토폴로지 위치에 할당된 실제 IP 주소 집합 해석 |
| **58** | `bf.q.resolveLocationSpecifier()` | `show ip interface brief` | Specifier Resolver | `Location` | 위치 명세자에 매칭되는 토폴로지 위치 객체 해석 |
| **59** | `bf.q.resolveNodeSpecifier()` | `show hosts` | Specifier Resolver | `Node` | 노드 명세자(정규식/그룹)에 일치하는 대상 장비 호스트명 목록 해석 |
| **60** | `bf.q.routes()` | `show ip route` | Layer 3 (Underlay Routing) | `Node, VRF, Network, Next_Hop, Protocol, Metric, Admin_Distance` | 통합 라우팅 테이블(RIB) 활성 경로 및 Next-Hop 검증 |
| **61** | `bf.q.searchFilters()` | `show ip access-lists` | Layer 3 (Security Filter) | `Node, Filter_Name, Flow, Action, Line_Content` | 특정 조건(예: 포트 179 차단)을 만족하는 패킷을 허용/차단하는 ACL 및 라인 역추적 |
| **62** | `bf.q.searchRoutePolicies()` | `show route-map` | Layer 3 (Policy Routing) | `Node, Policy_Name, Action, Output_Route` | Route-Map 및 라우트 정책에서 특정 접두사를 허용/거부/변조하는 조건 역추적 |
| **63** | `bf.q.snmpCommunityClients()` | `show snmp community` | Device Management | `Node, Community, Reason` | SNMP 커뮤니티 문자열 및 NMS IP 접근 제어 목록 검증 |
| **64** | `bf.q.subnetMultipathConsistency()` | `show ip cef <subnet>` | Layer 3 (Underlay Routing) | `Flow, Traces` | 서브넷 내 호스트별 ECMP 포워딩 경로 일관성 검증 |
| **65** | `bf.q.switchedVlanProperties()` | `show vlan brief` | Layer 2 (Data Link) | `Node, Interface, Access_VLAN, Trunk_VLANs` | 스위치포트 VLAN 구성, Access/Trunk 모드 및 허용 VLAN 목록 검증 |
| **66** | `bf.q.testFilters()` | `show ip access-lists <acl_name>` | Layer 3 (Security Filter) | `Node, Filter_Name, Flow, Action, Line_Content, Trace` | 가상 패킷 헤더를 ACL에 통과시켜 몇 번 라인에서 PERMIT/DENY 되는지 행동 검증 |
| **67** | `bf.q.testRoutePolicies()` | `show route-map` | Layer 3 (Policy Routing) | `Node, Policy_Name, Input_Route, Action, Output_Route` | 가상 라우트에 대해 Route-Map 정책을 적용했을 때의 변조 결과 시뮬레이션 |
| **68** | `bf.q.traceroute()` | `traceroute <dst> source <src>` | Layer 4 (Transport & Forwarding) | `Flow, Traces, TraceCount` | 특정 패킷 헤더(IP, 포트, 프로토콜)의 단방향 홉별 전달 및 드롭 위치 추적 |
| **69** | `bf.q.transferBDDValidation()` | `show ip cef` | Layer 3 (Underlay Routing) | `Node, Status` | 심볼릭 BDD 엔진과 실제 시뮬레이션 간의 수학적 전달 동등성 검증 |
| **70** | `bf.q.undefinedReferences()` | `show running-config` | Config Hygiene | `Node, Structure_Type, Structure_Name, Context` | 참조되고 있으나 실제 정의되지 않은 객체(존재하지 않는 ACL 호출) 탐지 |
| **71** | `bf.q.unusedStructures()` | `show running-config` | Config Hygiene | `Node, Structure_Type, Structure_Name` | 정의되어 있으나 어떤 인터페이스에서도 사용되지 않는 미사용 정책 탐지 |
| **72** | `bf.q.userProvidedLayer1Edges()` | `show cdp neighbors detail` | Layer 1 (Physical) | `Interface, Remote_Interface` | 사용자가 수동 제공한 물리 케이블링 토폴로지 매핑 검증 |
| **73** | `bf.q.viConversionStatus()` | `show version` | Model Conversion | `Node, Status` | 장비 설정이 Batfish 표준 벤더 중립 모델로 정상 변환되었는지 검증 |
| **74** | `bf.q.viConversionWarning()` | `show running-config` | Model Conversion | `Node, Warning` | 벤더 중립 모델 변환 과정에서 누락된 속성 경고 분석 |
| **75** | `bf.q.viModel()` | `show running-config` | Model Conversion | `Answer (JSON Model)` | 벤더 중립 표준 모델로 변환된 노드 및 인터페이스 속성 덤프 |
| **76** | `bf.q.vrrpProperties()` | `show vrrp brief` | Layer 3 (FHRP) | `Interface, Group, Virtual_IP, Priority, Master_Node` | VRRP 그룹 번호, 가상 IP, Priority 및 Master/Backup 상태 검증 |
| **77** | `bf.q.vxlanEdges()` | `show nve peers` | Layer 3 (Overlay) | `Node, VTEP_Address, Remote_Node, Remote_VTEP` | VXLAN 터널 엔드포인트(VTEP) 간의 NVE 피어링 엣지 검증 |
| **78** | `bf.q.vxlanVniProperties()` | `show nve vni` | Layer 3 (Overlay) | `Node, VNI, Multicast_Group, Interface` | VXLAN VNI 매핑, 멀티캐스트 그룹 및 바인딩 인터페이스 검증 |

