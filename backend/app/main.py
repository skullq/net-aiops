import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.models import (
    AppConfig,
    ChatRequest,
    CommandExecutionRequest,
    DeviceConfig,
    EdgeModel,
    GraphDataResponse,
    LLMConfig,
    NodeModel,
    RemediationRequest,
)
from app.config import settings
from app.device_manager import device_manager, ManagedDevice
from app.graph_engine import graph_engine
from app.mcp_iosxe_server import mcp_tool
from app.ai_agent import AIAgentOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("net_aiops")

# 앱 전역 설정 인스턴스 (.env 기반 기본값 로드)
current_app_config = settings.to_app_config()

# 등록 장비 인벤토리 동기화
all_devs = device_manager.get_all_devices()
first_dev = all_devs[0] if all_devs else ManagedDevice(id="r1", name="r1", host="192.168.100.11", mock_mode=False)
current_app_config.device = DeviceConfig(
    host=first_dev.host,
    port=first_dev.port or 22,
    username=first_dev.username or "admin",
    password=first_dev.password or "admin",
    enable_password=first_dev.enable_password or "admin",
    mock_mode=first_dev.mock_mode if first_dev.mock_mode is not None else False,
)

# MCP 도구 초기 디바이스 설정 적용
mcp_tool.update_config(current_app_config.device)

# AI 에이전트 오케스트레이터 초기화
ai_orchestrator = AIAgentOrchestrator(graph_engine=graph_engine, mcp_tool=mcp_tool)

# FastAPI 앱 생성
app = FastAPI(
    title="Net-AIOps Studio Backend",
    version="1.0.0",
    description="Python uv 기반 FastAPI 서버 - NetworkX Causal Graph & Cisco IOS-XE Scrapli/Hier-Config MCP 엔진"
)

# CORS 설정 (Next.js 프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    devs = device_manager.get_all_devices()
    return {
        "status": "healthy",
        "service": "Net-AIOps Studio Backend",
        "graph_nodes_count": graph_engine.graph.number_of_nodes(),
        "graph_edges_count": graph_engine.graph.number_of_edges(),
        "registered_devices_count": len(devs),
        "devices": [{"id": d.id, "name": d.name, "host": d.host, "mock_mode": d.mock_mode} for d in devs]
    }


# ==========================================
# 1. GraphDB Studio & Visualizer Endpoints
# ==========================================

@app.get("/api/graph", response_model=GraphDataResponse)
def get_graph():
    """NetworkX DiGraph 전체 데이터를 react-force-graph-2d 규격(nodes, links)으로 반환합니다."""
    return graph_engine.get_graph_data()


@app.post("/api/graph/nodes")
def add_or_update_node(node: NodeModel):
    """새로운 노드를 추가하거나 기존 노드 속성을 갱신합니다."""
    graph_engine.add_node(node)
    return {"success": True, "message": f"Node '{node.id}' added/updated successfully."}


@app.delete("/api/graph/nodes/{node_id}")
def delete_node(node_id: str):
    """노드 및 연결된 엣지를 삭제합니다."""
    removed = graph_engine.delete_node(node_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return {"success": True, "message": f"Node '{node_id}' removed successfully."}


@app.post("/api/graph/edges")
def add_edge(edge: EdgeModel):
    """두 노드 간의 방향성 엣지를 추가합니다."""
    graph_engine.add_edge(edge)
    return {"success": True, "message": f"Edge '{edge.source}' -> '{edge.target}' added successfully."}


@app.delete("/api/graph/edges")
def delete_edge(source: str = Query(...), target: str = Query(...)):
    """두 노드 간의 엣지를 삭제합니다."""
    removed = graph_engine.delete_edge(source, target)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Edge '{source}' -> '{target}' not found.")
    return {"success": True, "message": f"Edge '{source}' -> '{target}' removed successfully."}


@app.post("/api/graph/reset")
def reset_graph():
    """그래프를 기본 Cisco IOS-XE 장애 진단 시드 데이터로 재설정합니다."""
    graph_engine.reset_to_default()
    return {"success": True, "message": "Graph reset to default scenario data."}


@app.get("/api/graph/paths/{node_id}")
def get_causal_paths(node_id: str):
    """특정 노드로부터 연결되는 모든 인과 관계 경로를 탐색합니다."""
    paths = graph_engine.find_causal_paths(node_id)
    return {"node_id": node_id, "paths_count": len(paths), "paths": paths}


# ==========================================
# 2. LLM & IOS-XE Connection Settings Endpoints
# ==========================================

@app.get("/api/config", response_model=AppConfig)
def get_config():
    """현재 LLM 및 Cisco IOS-XE 장비 연결 설정을 조회합니다."""
    active = device_manager.get_active_device()
    current_app_config.device = DeviceConfig(
        host=active.host,
        port=active.port,
        username=active.username,
        password=active.password or "",
        enable_password=active.enable_password or "",
        mock_mode=active.mock_mode,
    )
    # 보안상 API Key 마스킹 처리하여 반환
    safe_config = current_app_config.model_copy(deep=True)
    if safe_config.llm.api_key:
        key = safe_config.llm.api_key
        safe_config.llm.api_key = f"{key[:3]}...{key[-4:]}" if len(key) > 7 else "***"
    return safe_config


@app.post("/api/config")
def update_config(new_config: AppConfig):
    """LLM 및 IOS-XE 장비 접속 설정을 업데이트합니다."""
    global current_app_config
    # API 키가 마스킹된 채로 재전송된 경우 기존 키 유지
    if new_config.llm.api_key.startswith("***") or "..." in new_config.llm.api_key:
        new_config.llm.api_key = current_app_config.llm.api_key

    current_app_config = new_config
    mcp_tool.update_config(new_config.device)
    logger.info("Application LLM and Device configuration updated.")
    return {"success": True, "message": "Configuration updated successfully."}


# ==========================================
# 3. Cisco IOS-XE Device Management Endpoints
# ==========================================

@app.get("/api/devices")
def get_devices():
    """등록된 모든 Cisco IOS-XE 장비 목록 및 기본 접속정보 반환"""
    all_devs = device_manager.get_all_devices()
    defaults = device_manager.get_default_credentials()
    return {
        "devices": all_devs,
        "default_credentials": defaults,
        "total_count": len(all_devs)
    }


@app.post("/api/devices")
def add_device(device: ManagedDevice):
    """새로운 Cisco IOS-XE 장비 등록"""
    saved = device_manager.add_device(device)
    return {"success": True, "device": saved, "message": f"장비 '{saved.name}' 등록 완료"}


@app.put("/api/devices/{device_id}")
def update_device(device_id: str, data: Dict[str, Any]):
    """장비 설정 변경 (이름, IP, 포트, 계정, 비밀번호, Mock 여부 등)"""
    updated = device_manager.update_device(device_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    return {"success": True, "device": updated, "message": f"장비 '{updated.name}' 설정 변경 완료"}


@app.delete("/api/devices/{device_id}")
def delete_device(device_id: str):
    """장비 삭제"""
    deleted = device_manager.delete_device(device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    return {"success": True, "message": "장비가 성공적으로 삭제되었습니다."}


# ==========================================
# 4. IOS-XE MCP Tool Direct Execution
# ==========================================

@app.post("/api/mcp/execute")
def execute_show_command(req: CommandExecutionRequest):
    """Scrapli + ntc-templates 기반 Show 명령어 실행 및 JSON 파싱 테스트 엔드포인트"""
    result = mcp_tool.execute_show_command(req.command, use_textfsm=req.use_textfsm)
    return result


@app.post("/api/mcp/remediation")
def generate_remediation(req: RemediationRequest):
    """hier-config 기반 교정 CLI 스크립트 도출 테스트 엔드포인트"""
    result = mcp_tool.generate_remediation_cli(
        running_config=req.running_config,
        target_config=req.target_config,
        hostname=req.hostname
    )
    return result


# ==========================================
# 4. Unified AI Chat & Real-time Trace SSE Stream
# ==========================================

@app.post("/api/chat")
async def chat_sse_stream(request: Request, chat_req: ChatRequest):
    """AI 채팅 및 실시간 추론(Trace)/Graph/MCP 이벤트 SSE 스트리밍 엔드포인트."""
    llm_cfg = chat_req.llm_config or current_app_config.llm
    dev_cfg = chat_req.device_config or current_app_config.device

    async def event_generator():
        try:
            async for event in ai_orchestrator.stream_chat_response(
                message=chat_req.message,
                history=chat_req.history,
                llm_config=llm_cfg,
                device_config=dev_cfg
            ):
                # 클라이언트 연결 끊김 확인
                if await request.is_disconnected():
                    logger.info("Client disconnected from SSE stream.")
                    break
                yield event
        except Exception as e:
            logger.error(f"Error during SSE chat generation: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": f'{{"error": "{str(e)}"}}'
            }

    return EventSourceResponse(event_generator())
