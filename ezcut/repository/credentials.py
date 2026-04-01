from importlib import import_module
from typing import Any

SERVICE_NAME = "ezcut-mattermost"


class CredentialRepository:
    def __init__(self, service_name: str = SERVICE_NAME) -> None:
        self.service_name = service_name

    def get_password(self, email: str) -> str | None:
        keyring = self._load_keyring()
        return keyring.get_password(self.service_name, self._normalize_account(email))

    def set_password(self, email: str, password: str) -> None:
        keyring = self._load_keyring()
        keyring.set_password(
            self.service_name,
            self._normalize_account(email),
            password,
        )

    def has_password(self, email: str) -> bool:
        return self.get_password(email) is not None

    def delete_password(self, email: str) -> None:
        keyring = self._load_keyring()
        account = self._normalize_account(email)

        try:
            keyring.delete_password(self.service_name, account)
        except Exception as error:
            if error.__class__.__name__ != "PasswordDeleteError":
                raise

    @staticmethod
    def _load_keyring() -> Any:
        try:
            return import_module("keyring")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "keyring 패키지가 설치되지 않았습니다. 자격 증명 저장소를 사용하려면 keyring이 필요합니다."
            ) from error

    @staticmethod
    def _normalize_account(email: str) -> str:
        return email.strip().lower()
