from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    SYMPTOM = "Symptom"
    ROOT_CAUSE = "RootCause"
    VERIFICATION = "Verification"
    COMMAND = "Command"
    REMEDIATION = "Remediation"


class NodeModel(BaseModel):
    id: str
    label: str
    type: NodeType
    description: Optional[str] = ""
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    x: Optional[float] = None
    y: Optional[float] = None
    fx: Optional[float] = None
    fy: Optional[float] = None


class EdgeModel(BaseModel):
    source: str
    target: str
    relationship: Optional[str] = "leads_to"
    description: Optional[str] = ""


class GraphDataResponse(BaseModel):
    nodes: List[NodeModel]
    links: List[EdgeModel]
    layout: Optional[str] = "force"
    metadata: Optional[Dict[str, Any]] = None


class LLMConfig(BaseModel):
    base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI compatible Base URL")
    api_key: str = Field(default="", description="API Key")
    model: str = Field(default="gpt-4o", description="Model name")


class DeviceConfig(BaseModel):
    host: str = Field(default="192.168.100.11", description="Cisco IOS-XE Host/IP")
    port: int = Field(default=22, description="SSH Port")
    username: str = Field(default="admin", description="SSH Username")
    password: str = Field(default="admin", description="SSH Password")
    enable_password: Optional[str] = Field(default="", description="Enable Password")


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    debug_mode: bool = Field(default=True, description="Enable debug logging of sessions to disk")


class CommandExecutionRequest(BaseModel):
    command: str
    use_textfsm: bool = True


class RemediationRequest(BaseModel):
    running_config: str
    target_config: str
    hostname: str = "CSR1000v"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    llm_config: Optional[LLMConfig] = None
    device_config: Optional[DeviceConfig] = None
    language: Optional[str] = Field(default="ko", description="Response language ('ko' or 'en')")
    debug_mode: Optional[bool] = Field(default=None, description="Override debug logging mode for this session")
