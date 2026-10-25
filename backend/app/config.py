import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.models import AppConfig, DeviceConfig, LLMConfig

# .env 파일 위치 탐색 (backend/.env 우선, 없으면 프로젝트 루트 .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
ROOT_ENV_PATH = BASE_DIR.parent / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
elif ROOT_ENV_PATH.exists():
    load_dotenv(dotenv_path=ROOT_ENV_PATH)
else:
    load_dotenv()


def str_to_bool(val: Optional[str], default: bool = True) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "t", "y")


class ServerSettings(BaseModel):
    host: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "3001")))
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
    )


class EnvironmentSettings(BaseModel):
    """ .env 파일 기반 초기 설정 로더 """
    server: ServerSettings = Field(default_factory=ServerSettings)
    
    # LLM Settings (Supports Gemini, OpenAI, and compatible providers)
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini")
    )
    openai_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "LLM_BASE_URL",
            os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        )
    )
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv(
            "LLM_API_KEY",
            os.getenv("OPENAI_API_KEY", "")
        )
    )
    openai_model: str = Field(
        default_factory=lambda: os.getenv(
            "LLM_MODEL",
            os.getenv("OPENAI_MODEL", "gemini-flash-lite-latest")
        )
    )

    # Cisco IOS-XE Device Settings (Default to Lab Core Router r1)
    cisco_host: str = Field(
        default_factory=lambda: os.getenv("CISCO_HOST", "192.168.100.11")
    )
    cisco_port: int = Field(
        default_factory=lambda: int(os.getenv("CISCO_PORT", "22"))
    )
    cisco_username: str = Field(
        default_factory=lambda: os.getenv("CISCO_USERNAME", "admin")
    )
    cisco_password: str = Field(
        default_factory=lambda: os.getenv("CISCO_PASSWORD", "admin")
    )
    cisco_enable_password: str = Field(
        default_factory=lambda: os.getenv("CISCO_ENABLE_PASSWORD", "admin")
    )
    debug_mode: bool = Field(
        default_factory=lambda: str_to_bool(os.getenv("DEBUG_MODE", "true"), default=True)
    )

    def to_app_config(self) -> AppConfig:
        """Pydantic AppConfig 인스턴스로 변환"""
        return AppConfig(
            llm=LLMConfig(
                base_url=self.openai_base_url,
                api_key=self.openai_api_key,
                model=self.openai_model,
            ),
            device=DeviceConfig(
                host=self.cisco_host,
                port=self.cisco_port,
                username=self.cisco_username,
                password=self.cisco_password,
                enable_password=self.cisco_enable_password,
            ),
            debug_mode=self.debug_mode,
        )


settings = EnvironmentSettings()
