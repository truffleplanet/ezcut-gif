from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service

from ezcut.repository.config import AppConfig
from ezcut.repository.credentials import CredentialRepository
from ezcut.store.models import UploadConfig, UploadResult
from ezcut.store.state import ProgressCallback
from ezcut.utils.emoji_txt import list_image_files


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
        self.files: list = []

    def run(self) -> UploadResult:
        """업로드 작업을 실행하고 결과를 반환한다."""
        self.files = list_image_files(self.config.directory)
        self.files = self.files[self.config.start_index - 1 :]
        if self.config.limit is not None:
            self.files = self.files[: self.config.limit]

        if not self.files:
            raise ValueError("조건에 맞는 업로드 대상 파일이 없습니다.")

        add_url = self._resolve_add_url()
        driver = self._build_driver()

        try:
            self._wait_for_manual_login(driver, add_url)
        finally:
            driver.quit()

        return UploadResult(success=0, failed=[])

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
        options = ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1600,1200")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if self.config.user_data_dir:
            options.add_argument(f"--user-data-dir={self.config.user_data_dir}")
        if self.config.profile_directory:
            options.add_argument(f"--profile-directory={self.config.profile_directory}")

        return webdriver.Chrome(options=options, service=Service())

    def _wait_for_manual_login(self, driver, add_url: str) -> None:
        """사용자가 직접 로그인할 수 있도록 대기한다."""
        driver.get(add_url)
        print("브라우저가 열렸습니다.")
        print("meeting.ssafy 로그인 상태가 아니라면 직접 로그인한 뒤 Enter를 누르세요.")
        input()
        driver.get(add_url)

    def _open_add_page(self, driver, wait, add_url: str) -> None:
        """이모지 업로드 페이지를 연다."""
        raise NotImplementedError

    def _upload_one(
        self, driver, wait, add_url: str, image_path, emoji_name: str
    ) -> None:
        """이미지 하나를 업로드한다."""
        raise NotImplementedError
