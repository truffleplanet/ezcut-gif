from __future__ import annotations

from importlib import import_module
from typing import Any

SERVICE_NAME = "ezcut-mattermost"


class CredentialRepository:
    def __init__(self, service_name: str = SERVICE_NAME) -> None:
        self.service_name = service_name

    def get_password(self, username: str) -> str | None:
        keyring = self._load_keyring()
        return keyring.get_password(self.service_name, username)

    def set_password(self, username: str, password: str) -> None:
        keyring = self._load_keyring()
        keyring.set_password(self.service_name, username, password)

    def delete_password(self, username: str) -> None:
        keyring = self._load_keyring()
        keyring.delete_password(self.service_name, username)

    @staticmethod
    def _load_keyring() -> Any:
        try:
            return import_module("keyring")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "keyring 패키지가 설치되지 않았습니다. 자격 증명 저장소를 사용하려면 keyring이 필요합니다."
            ) from error
