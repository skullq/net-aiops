from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    SYMPTOM = "Symptom"
    ROOT_CAUSE = "RootCause"
    VERIFICATION = "Verification"
    COMMAND = "Command"


class NodeModel(BaseModel):
    id: str
    label: str
    type: NodeType
    description: Optional[str] = ""
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EdgeModel(BaseModel):
    source: str
    target: str
    relationship: Optional[str] = "leads_to"
    description: Optional[str] = ""


class GraphDataResponse(BaseModel):
    nodes: List[NodeModel]
    links: List[EdgeModel]


class LLMConfig(BaseModel):
    base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI compatible Base URL")
    api_key: str = Field(default="", description="API Key")
    model: str = Field(default="gpt-4o", description="Model name")


class DeviceConfig(BaseModel):
    host: str = Field(default="192.168.1.1", description="Cisco IOS-XE Host/IP")
    port: int = Field(default=22, description="SSH Port")
    username: str = Field(default="cisco", description="SSH Username")
    password: str = Field(default="cisco", description="SSH Password")
    enable_password: Optional[str] = Field(default="", description="Enable Password")
    mock_mode: bool = Field(default=True, description="Enable simulated IOS-XE responses")


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    device: DeviceConfig = Field(default_factory=DeviceConfig)


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
