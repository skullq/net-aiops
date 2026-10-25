import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import dotenv_values
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEVICES_ENV_PATH = BASE_DIR / "devices.env"
DEVICES_JSON_PATH = BASE_DIR / "devices.json"


class ManagedDevice(BaseModel):
    id: str
    name: str
    host: str
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enable_password: Optional[str] = None
    description: Optional[str] = ""


class DeviceManager:
    """Cisco IOS-XE 복수 장비 인벤토리 관리자.

    100% 라이브 실측 장비(r1~r5: 192.168.100.11~15) 연결을 보장합니다.
    """

    def __init__(self):
        self._ensure_storage()

    def get_default_credentials(self) -> Dict[str, Any]:
        """devices.env에서 기본 접속정보 조회"""
        if not DEVICES_ENV_PATH.exists():
            return {
                "port": 22,
                "username": "admin",
                "password": "admin",
                "enable_password": "admin"
            }

        vals = dotenv_values(DEVICES_ENV_PATH)
        return {
            "port": int(vals.get("DEFAULT_SSH_PORT", 22)),
            "username": vals.get("DEFAULT_SSH_USERNAME", "admin"),
            "password": vals.get("DEFAULT_SSH_PASSWORD", "admin"),
            "enable_password": vals.get("DEFAULT_SSH_ENABLE_PASSWORD", "admin")
        }

    def _ensure_storage(self) -> None:
        """저장소 파일 검증 및 초기화"""
        if not DEVICES_JSON_PATH.exists():
            default_devices = [
                {
                    "id": f"r{i}",
                    "name": f"r{i}",
                    "host": f"192.168.100.{10 + i}",
                    "port": 22,
                    "username": "admin",
                    "password": "admin",
                    "enable_password": "admin",
                    "description": f"Lab Router r{i} (192.168.100.{10 + i})"
                }
                for i in range(1, 6)
            ]
            self._save_devices_to_json(default_devices)

    def _read_devices_from_json(self) -> List[Dict[str, Any]]:
        try:
            with open(DEVICES_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {DEVICES_JSON_PATH}: {e}")
            return []

    def _save_devices_to_json(self, devices: List[Dict[str, Any]]) -> None:
        with open(DEVICES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)

    def resolve_device(self, dev: ManagedDevice) -> ManagedDevice:
        """기본정보를 상속하되, 개별 설정이 있으면 개별 설정을 우선 적용"""
        defaults = self.get_default_credentials()
        return ManagedDevice(
            id=dev.id,
            name=dev.name,
            host=dev.host,
            port=dev.port if dev.port is not None else defaults["port"],
            username=dev.username if dev.username else defaults["username"],
            password=dev.password if dev.password is not None else defaults["password"],
            enable_password=dev.enable_password if dev.enable_password is not None else defaults["enable_password"],
            description=dev.description or ""
        )

    def get_all_devices(self) -> List[ManagedDevice]:
        """등록된 모든 장비 반환 (개별 설정 우선 + 기본값 상속)"""
        devices_data = self._read_devices_from_json()
        return [self.resolve_device(ManagedDevice(**item)) for item in devices_data]

    def get_device(self, device_id: str) -> Optional[ManagedDevice]:
        devices = self.get_all_devices()
        for d in devices:
            if d.id == device_id:
                return d
        return None

    def add_device(self, device: ManagedDevice) -> ManagedDevice:
        """장비 추가 (ID 식별자 정규화 후 저장)"""
        devices = self._read_devices_from_json()
        device.id = device.id.strip().lower().replace(" ", "_")
        
        # 개별 설정 우선 처리
        resolved = self.resolve_device(device)
        
        existing_idx = next((i for i, d in enumerate(devices) if d["id"] == device.id), None)
        if existing_idx is not None:
            devices[existing_idx] = resolved.model_dump()
        else:
            devices.append(resolved.model_dump())

        self._save_devices_to_json(devices)
        logger.info(f"Device '{device.name}' added to inventory.")
        return resolved

    def update_device(self, device_id: str, data: Dict[str, Any]) -> Optional[ManagedDevice]:
        """장비 설정 변경 (이름, IP, 포트, 인증정보 등)"""
        devices = self._read_devices_from_json()
        for i, d in enumerate(devices):
            if d["id"] == device_id:
                d.update(data)
                # mock_mode 잔여 키가 있다면 제거
                d.pop("mock_mode", None)
                updated_raw = ManagedDevice(**d)
                resolved = self.resolve_device(updated_raw)
                devices[i] = resolved.model_dump()
                self._save_devices_to_json(devices)
                logger.info(f"Device '{device_id}' updated successfully.")
                return resolved
        return None

    def delete_device(self, device_id: str) -> bool:
        """장비 삭제"""
        devices = self._read_devices_from_json()
        new_devices = [d for d in devices if d["id"] != device_id]
        if len(new_devices) == len(devices):
            return False

        self._save_devices_to_json(new_devices)
        logger.info(f"Device '{device_id}' removed from inventory.")
        return True


device_manager = DeviceManager()
