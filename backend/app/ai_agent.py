"""LangGraph 기반 AIOps 자율 오케스트레이션 어댑터 (ai_agent.py).

레거시 절차적 코드를 완전히 걷어내고, LangGraph 기반의 상태 그래프(StateGraph) 워크플로우로
모든 진단(Scope Detection -> Causal Routing -> Batfish Formal Verification -> Live CLI Telemetry -> LLM Synthesis)을
완전히 처리합니다.
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.models import ChatMessage, DeviceConfig, LLMConfig
from app.graph_engine import CausalGraphEngine
from app.mcp_iosxe_server import IOSXEMCPTool
from app.langgraph_agent import langgraph_agent

logger = logging.getLogger(__name__)


class AIAgentOrchestrator:
    """LangGraph 기반 자율 AIOps 오케스트레이터."""

    def __init__(self, graph_engine: Optional[CausalGraphEngine] = None, mcp_tool: Optional[IOSXEMCPTool] = None):
        self.graph_engine = graph_engine
        self.mcp_tool = mcp_tool
        self.agent = langgraph_agent

    async def stream_chat_response(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        llm_config: Optional[LLMConfig] = None,
        device_config: Optional[DeviceConfig] = None,
        language: str = "ko",
        debug_mode: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """LangGraph 워크플로우를 실행하고 실시간 SSE 이벤트를 스트리밍합니다."""
        logger.info(f"[LangGraph-AIOps] Starting diagnostic workflow for: '{message}' (lang={language}, debug_mode={debug_mode})")
        async for event in self.agent.stream_diagnostic_workflow(
            message=message,
            history=history,
            llm_config=llm_config,
            device_config=device_config,
            language=language,
            debug_mode=debug_mode
        ):
            yield event
