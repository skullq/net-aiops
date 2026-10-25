# Net-AIOps Studio 🚀
> **Cisco IOS-XE Causal GraphDB & Multi-Agent Operations Platform**

NetworkX DiGraph 인과관계 지식 그래프와 Cisco IOS-XE Scrapli / hier-config MCP 엔진, 그리고 Next.js 3-패널 인터페이스를 결합한 차세대 네트워크 자동화 및 AIOps 스튜디오입니다.

---

## 🏛️ 아키텍처 개요

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Net-AIOps Studio Web UI                         │
│                    (Next.js App Router + Tailwind)                     │
├─────────────────────┬──────────────────────────┬───────────────────────┤
│ [좌측 창]           │ [중앙 창]                │ [우측 창]             │
│ GraphDB Studio      │ 통합 AI 채팅             │ 실시간 Trace 뷰어     │
│ (react-force-graph) │ (Causal 추론 & MCP 연동) │ (Timeline & Raw JSON) │
└──────────┬──────────┴────────────┬─────────────┴───────────┬───────────┘
           │                       │                         │
           ▼                       ▼                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     FastAPI 백엔드 서버 (Python uv)                    │
│                                                                        │
│  • NetworkX DiGraph Causal Graph Engine (Symptom/RootCause/Command)    │
│  • Cisco IOS-XE MCP Tool (Scrapli + ntc-templates + hier-config)       │
│  • Real-time SSE Diagnostic Agent (Trace & Streaming Event Source)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 주요 기능

### 1. [좌측 창] GraphDB Studio & Visualizer
- **NetworkX (`nx.DiGraph`) 실시간 시각화**: `react-force-graph-2d` 기반 인터랙티브 캔버스.
- **4대 Causal 노드 규격**:
  - 🟡 **Symptom (이상 징후)**: BGP Neighbor Down, OSPF ExStart 고착, CRC Input 에러 등
  - 🔴 **RootCause (근본 원인)**: MD5 불일치, MTU Mismatch, Duplex 불일치 등
  - 🔵 **Verification (검증 절차)**: 상태 점검 및 진단 가설 확인
  - 🟢 **Command (실행 CLI)**: Scrapli 확인 명령어 및 hier-config 교정 명령어
- **즉시 반영 CRUD**: 노드 및 방향성 엣지를 간단한 모달 폼으로 추가/삭제.

### 2. [상단 바] Cisco IOS-XE 장치 관리 (Device Manager) & `devices.env`
- **독립된 환경파일 (`backend/devices.env`)**:
  - 기본 설정(`CISCO_DEFAULT_HOST`, `CISCO_DEFAULT_PORT` 등)이 정의되어 있으면 **시스템 초기화 및 진단 시 최우선(Priority 1)**으로 자동 적용됩니다.
- **다중 접속 장비 관리**:
  - 복수의 라우터를 목록으로 등록/조회/삭제하고 원하는 장비를 실시간 타깃으로 즉시 활성화.
  - 임의의 장비를 언제든지 **[기본값으로 저장]**하여 `devices.env` 파일에 영구 동기화 가능.

### 3. [상단 바] LLM 연결 설정 모달
- **Google Gemini & OpenAI 호환 Provider**: Base URL, API Key, Model명(`gemini-flash-lite-latest` 등) 설정.

### 3. [백엔드] Cisco IOS-XE MCP 엔진
- **Scrapli (`cisco_iosxe`) + `ntc-templates`**: `show` 명령어를 실행하고 TextFSM 템플릿을 통해 JSON 구조체로 자동 파싱.
- **`hier-config` Remediation**: 현재 `running-config`와 목표 `target-config`의 계층적 차분을 분석하여 멱등적(Idempotent) 복구 CLI 명령어 생성.

### 4. [중앙 창] 통합 AI 진단 채팅 & [우측 창] 실시간 진행상황(Trace) 뷰어
- **원클릭 추천 진단 프롬프트** (BGP Down / OSPF ExStart / CRC Drop).
- **실시간 SSE 스트리밍**:
  1. `Intent Analysis`: 질문 의도 및 대상 프로토콜 식별
  2. `GraphDB Traversal`: Causal Graph에서 증상 ➔ 원인 ➔ 검증 경로 도출
  3. `Scrapli MCP Execution`: 장비 상태 수집 및 TextFSM 구조화 파싱
  4. `TextFSM JSON Inspector`: 원시 JSON 트리 뷰어 및 Raw CLI 출력 탭
  5. `hier-config Remediation`: 멱등적 Cisco 복구 CLI 코드 블록 생성
  6. `LLM Synthesis`: 종합 진단 보고서 실시간 마크다운 스트리밍

---

## 🚀 빠른 시작 가이드

### 1. 백엔드 실행 (`FastAPI`)
```bash
cd /root/Net-AIOps/backend

# uv 가상환경 생성 및 패키지 설치
uv venv --python 3.12 .venv
uv pip install -e .

# 환경변수 설정 (.env)
cp .env.example .env

# FastAPI 서버 구동 (포트 3001)
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

### 2. 프론트엔드 실행 (`Next.js`)
```bash
cd /root/Net-AIOps/frontend

# 환경변수 설정 (.env.local)
cp .env.example .env.local

# 개발 서버 구동 (포트 3000)
npm run dev
```

### 3. 주요 환경변수 (`backend/.env`)

| 변수명 | 기본값 | 설명 |
|---|---|---|
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI 호환 Base URL |
| `OPENAI_API_KEY` | *(빈값)* | LLM API 키 (비워둘 시 내장 Causal 진단 엔진 동작) |
| `OPENAI_MODEL` | `gpt-4o` | 추론 모델명 |
| `CISCO_HOST` | `192.168.10.1` | Cisco IOS-XE 타깃 호스트/IP |
| `CISCO_PORT` | `22` | SSH 접속 포트 |
| `CISCO_USERNAME` | `admin` | SSH 계정명 |
| `CISCO_PASSWORD` | `cisco_password` | SSH 비밀번호 |
| `CISCO_MOCK_MODE` | `true` | 시뮬레이션 모드 활성화 여부 |
| `BACKEND_PORT` | `3001` | FastAPI 서비스 포트 |

### 4. 브라우저 접속
- **Web UI**: `http://localhost:3000`
- **FastAPI Swagger Docs**: `http://localhost:3001/docs`

