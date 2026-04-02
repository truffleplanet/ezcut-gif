from ezcut.repository.config import ConfigRepository
from ezcut.store.models import AppConfig


class ConfigService:
    """애플리케이션 설정을 관리하는 서비스."""

    def __init__(self, repository: ConfigRepository | None = None) -> None:
        self.repository = repository or ConfigRepository()

    def load_config(self) -> AppConfig:
        """현재 설정을 로드한다."""
        return self.repository.load()

    def save_config(self, config: AppConfig) -> None:
        """설정을 저장한다."""
        self.repository.save(config)

    def update_mattermost_email(self, email: str) -> AppConfig:
        """Mattermost 이메일을 업데이트하고 저장된 설정을 반환한다."""
        from dataclasses import replace

        config = self.load_config()
        updated = replace(config, mattermost_email=email)
        self.save_config(updated)
        return updated
