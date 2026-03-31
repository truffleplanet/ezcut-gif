from urllib.parse import urljoin

from ezcut.repository.config import AppConfig
from ezcut.repository.credentials import CredentialRepository
from ezcut.store.models import UploadConfig, UploadResult
from ezcut.store.state import ProgressCallback


class Uploader:
    """Mattermost 업로드 상태를 관리하는 서비스."""

    def __init__(
        self,
        config: UploadConfig,
        app_config: AppConfig | None = None,
        credentials: CredentialRepository | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self.app_config = app_config
        self.credentials = credentials
        self.on_progress = on_progress

    def run(self) -> UploadResult:
        """업로드 작업을 실행하고 결과를 반환한다."""
        raise NotImplementedError

    def _resolve_add_url(self) -> str:
        """업로드 페이지 주소를 계산한다."""
        if self.config.add_path.startswith(("http://", "https://")):
            return self.config.add_path
        return urljoin(
            f"{self.config.base_url.rstrip('/')}/",
            self.config.add_path.lstrip("/"),
        )

    def _build_driver(self):
        """업로드에 사용할 크롬 드라이버를 생성한다."""
        raise NotImplementedError

    def _wait_for_manual_login(self, driver, add_url: str) -> None:
        """사용자가 직접 로그인할 수 있도록 대기한다."""
        raise NotImplementedError

    def _open_add_page(self, driver, wait, add_url: str) -> None:
        """이모지 업로드 페이지를 연다."""
        raise NotImplementedError

    def _upload_one(
        self, driver, wait, add_url: str, image_path, emoji_name: str
    ) -> None:
        """이미지 하나를 업로드한다."""
        raise NotImplementedError
