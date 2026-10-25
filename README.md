# Net-AIOps Studio 🚀
> **Cisco IOS-XE Causal GraphDB & LangGraph 자율 네트워크 AIOps 플랫폼**

**Net-AIOps Studio**는 Cisco IOS-XE 대규모 네트워크 인프라에서 발생하는 복합 장애를 인과관계 그래프(Causal DiGraph), Batfish 정형 검증 엔진, Scrapli 실측 텔레메트리, 그리고 LangGraph 기반 다단계 추론 에이전트를 결합하여 **자율 진단부터 계층적 복원 CLI(hconfig) 생성 및 사후 검증까지 원스톱으로 수행하는 풀스택 AIOps 플랫폼**입니다.

---

## 🏛️ 시스템 아키텍처 (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Net-AIOps Studio Web UI                               │
│                         (Next.js 14 App Router + Tailwind)                      │
├──────────────────────────┬───────────────────────────┬──────────────────────────┤
│        [좌측 창]         │         [중앙 창]         │        [우측 창]         │
│   Graph Studio 캔버스    │      통합 AI 진단 채팅    │    실시간 추론 Trace     │
│ (Force/Hierarchy/Radial) │ (자연어 질의 & 토큰 스트림) │ (타임라인 & 실측 CLI)    │
└────────────┬─────────────┴─────────────┬─────────────┴────────────┬─────────────┘
             │                           │                          │
             ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI 백엔드 서버 (Port 3001)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  1. LangGraph 자율 에이전트 (Scope ➔ Routing ➔ Batfish ➔ Telemetry ➔ Synthesis)   │
│  2. Universal Causal Graph Engine (NetworkX DiGraph & openCypher In-Memory)     │
│  3. Batfish Formal Verification Engine (78개 Batfish Question 정형 검증 분석)  │
│  4. Cisco IOS-XE MCP Tool (Scrapli + TextFSM ntc-templates 실측 수집)          │
│  5. Hierarchical Remediation Engine (hier-config 기반 멱등 복원 CLI 자동 생성)    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ 빠른 시작 가이드 (Quick Start)

### 1. 통합 실행 스크립트 (`start.sh`)
프로젝트 루트 디렉터리에서 `start.sh`를 실행하면 **포트 점유 정리 ➔ 백엔드(3001) ➔ 프론트엔드(3000)**가 순차적으로 자동 기동됩니다.

```bash
cd /root/Net-AIOps
./start.sh
```

* **백그라운드 무중단 실행 (선택 사항)**:
  ```bash
  nohup ./start.sh > logs/studio.log 2>&1 &
  tail -f logs/studio.log
  ```
* **서비스 종료**:
  * 포그라운드 실행 시: 터미널에서 `Ctrl + C`
  * 백그라운드 실행 시: `fuser -k 3000/tcp 3001/tcp`

### 2. 개별 서비스 수동 실행

#### [백엔드 - FastAPI]
```bash
cd /root/Net-AIOps/backend
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e .
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

#### [프론트엔드 - Next.js]
```bash
cd /root/Net-AIOps/frontend
npm install
npm run dev -- -p 3000
```

---

## 🌐 접속 주소

* **Web UI (대시보드)**: [http://localhost:3000](http://localhost:3000)
* **REST API & Swagger 문서**: [http://localhost:3001/docs](http://localhost:3001/docs)

---

## 🔍 핵심 기능 및 워크플로우

### 1. LangGraph 기반 5단계 자율 진단 파이프라인
자연어 질의(예: *"r1과 r2 사이의 네트워크 문제를 찾아줘"*) 수신 시 다음 5단계를 거쳐 실시간 SSE 스트리밍으로 결과를 도출합니다:

1. **Step 1: Scope Detection (동적 토폴로지 & 프로토콜 분석)**
   * Batfish L3 Topology 및 NetworkX 최단 경로 탐색을 통해 단일 장비, 멀티홉 구간(`TRANSIT_PATH`), 백본 ECMP 경로 자동 식별.
   * 경로 상 중계 노드(`r4`, `r5` 등)를 자동 확장하고 활성 라우팅 프로토콜(OSPF, IS-IS, BGP 등) 자동 감지.
2. **Step 2: Causal Routing (인과관계 그래프 추론)**
   * 관측된 장애 증상(`Symptom`)으로부터 연결된 원인 후보군(`RootCause`), 검증 질문(`Verification`), 실측 명령어(`Command`)를 OSI 7계층 하위 계층부터 상위 계층 순으로 정렬.
3. **Step 3: Batfish Formal Verification (수학적 정형 검증)**
   * 장비 running-config를 실시간 수집/스냅샷 로드하여 설정 불일치(Area, MTU, Router-ID, Wide Metric 등) 및 ACL 차단, PBR 우회, RIB 미등록 여부를 100% 정형 검증.
   * 다중 결함 탐지(Multi-Fault Detection)를 통해 경로 상 모든 결함 장비를 전수 탐색.
4. **Step 4: Live Telemetry (실측 CLI 수집 및 TextFSM 구조화)**
   * Scrapli 드라이버로 실제 Cisco IOS-XE 장비에 접속하여 `show ip route`, `show ip interface brief` 등을 실행하고 ntc-templates로 JSON 파싱.
5. **Step 5: LLM Synthesis & Hierarchical Config (hconfig 복원 리포트 생성)**
   * 정형 검증 팩트와 실측 데이터를 결합하여 최종 진단 보고서 작성.
   * 결함 장비별로 OSPF 설정 스타일(Interface 지정 방식 vs router ospf 하위 network 선언 방식)을 감지하여 100% 규격에 부합하는 계층적 복원 CLI 및 사후 검증 명령어를 생성.

---

### 2. Graph Studio (인과 그래프 인터랙티브 캔버스)
네트워크 장애의 원인과 결과를 직관적으로 탐색하고 지식 베이스를 관리할 수 있는 스튜디오 환경을 제공합니다:

* **3대 레이아웃 모드 지원**:
  * 🌐 **Force Unified**: 물리 시뮬레이션 기반 자유 유기적 배치
  * 🌲 **Hierarchical (OSI Layered)**: 증상 ➔ 원인 ➔ 검증 ➔ 명령어 계층별 트리 배치
  * 🎯 **Radial Hub**: 주요 증상 노드를 중심 허브로 방사형 탐색
* **5대 인과 노드 규격**:
  * 🟡 **Symptom (이상 징후)**: BGP 세션 다운, OSPF 이웃 불능 등
  * 🔴 **RootCause (근본 원인)**: 인터페이스 ACL 차단, MTU 불일치, Router-ID 충돌 등
  * 🔵 **Verification (검증 단계)**: Batfish 정형 질문 및 OSI 계층 검증
  * 🟢 **Command (확인 CLI)**: 실측 show 명령어
  * 🟣 **Remediation (교정 조치)**: 계층형 복원 설정 CLI

---

### 3. GraphDB 익스포트 (Neo4j & ArangoDB)
인메모리 그래프 데이터를 외부 상용 GraphDB에 즉시 적재할 수 있도록 전용 익스포트 파일들을 제공합니다:

* 디렉터리: [`exports/`](./exports/)
* **Neo4j ([exports/neo4j/](./exports/neo4j))**:
  * `cisco_iosxe_causal_graph.cypher`: Multi-Label(`:CausalNode`, `:Symptom` 등) 및 타입화 관계(`:CAUSES`, `:VERIFIED_BY`)가 포함된 openCypher 스크립트.
  * `nodes.csv`, `edges.csv`: `neo4j-admin database import` 전용 헤더 CSV.
* **ArangoDB ([exports/arangodb/](./exports/arangodb))**:
  * `CausalNode.json`: ArangoDB Document Collection.
  * `CausalEdge.json`: ArangoDB Edge Collection.
  * `causal_graph_complete.json`: 통합 멀티모델 JSON.
  * `import_arangodb.sh`: 원클릭 `arangoimport` 셸 스크립트.

---

### 4. LLM 실시간 모델 동적 List-up (Settings)
* **모달 설정 (Settings Modal)**:
  * Google Gemini 및 OpenAI 규격의 API 키 입력 시, 디바운스(600ms)로 제공자 엔드포인트에 질의하여 현재 계정에서 사용 가능한 모델 목록(예: `gemini-2.5-flash`, `gemini-2.5-pro`, `gpt-4o` 등)을 실시간으로 가져옵니다.
  * 검색된 모델 수 배지 노출, 새로고침 버튼(`RefreshCw`), 추천 상위 모델 빠른 선택 칩 및 자동완성 콤보박스를 지원합니다.

---

### 5. 세션 영구 보관 & 트러블슈팅 재현 (Debug Mode)
* 상단 헤더의 **Debug Mode** 활성화 시, 진단 세션의 전체 Trace 이벤트와 실시간 수집 텔레메트리가 파일로 영구 보관됩니다:
  * JSON 상세 데이터: `logs/ai_diagnostics/{session_id}.json`
  * 터미널 CLI 리플레이 로그: `logs/ai_diagnostics/{session_id}.log`
* 터미널에서 즉시 재현:
  ```bash
  cat logs/ai_diagnostics/diag_YYYYMMDD_HHMMSS_xxxxxx.log
  ```

---

## 📁 주요 디렉터리 구조

```
Net-AIOps/
├── start.sh                      # 백엔드/프론트엔드 통합 기동 스크립트
├── batfish_support.md            # Batfish 78개 정형 검증 API 매핑 명세서
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 엔드포인트 및 SSE 스트리밍 라우터
│   │   ├── langgraph_agent.py    # LangGraph 5단계 자율 AIOps 워크플로우
│   │   ├── batfish_evaluator.py  # Batfish 스냅샷 및 78개 정형 검증 엔진
│   │   ├── graph_engine.py       # Universal Causal Graph Engine (NetworkX)
│   │   ├── mcp_iosxe_server.py   # Scrapli + TextFSM 텔레메트리 MCP 서버
│   │   ├── device_manager.py     # Cisco IOS-XE 장비 인벤토리 관리
│   │   └── config.py             # 시스템 환경설정 및 Pydantic 모델
│   └── devices.env               # 관리 대상 장비(r1~r5) 접속 설정
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx          # 3-패널 메인 레이아웃 및 SSE 수신 파서
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx     # AIOps 대화창 및 추천 시나리오
│   │   │   ├── TracePanel.tsx    # 실시간 진단 뷰어 및 TextFSM 탭
│   │   │   ├── GraphStudio.tsx   # 3D/2D 인과 그래프 시각화 및 노드/엣지 편집
│   │   │   ├── Header.tsx        # 네비게이션 헤더 및 디버그 토글
│   │   │   └── SettingsModal.tsx # LLM 동적 모델 선택 및 장비 설정 모달
│   │   └── i18n/                 # 한/영 다국어 리소스
└── exports/                      # GraphDB 포맷별 내보내기 결과물
    ├── neo4j/                    # Neo4j openCypher 및 CSV 임포트 파일
    └── arangodb/                 # ArangoDB JSON 컬렉션 및 arangoimport 스크립트
```

---

## 📜 라이선스 (License)
Apache License 2.0
