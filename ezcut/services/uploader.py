import time
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ezcut.repository.credentials import CredentialRepository
from ezcut.store.models import AppConfig, UploadConfig, UploadResult
from ezcut.store.state import ProgressCallback
from ezcut.utils.emoji_txt import list_image_files
from ezcut.utils.naming import normalize_emoji_name


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
        wait = WebDriverWait(driver, self.config.driver.wait_timeout_seconds)
        success = 0
        failed: list[tuple[Path, str]] = []

        try:
            self._login(driver, wait, add_url)
            total = len(self.files)

            for index, image_path in enumerate(self.files, start=1):
                emoji_name = normalize_emoji_name(
                    image_path.stem,
                    self.config.name_prefix,
                )

                if not emoji_name:
                    failed.append((image_path, "이모지 이름이 비어 있습니다."))
                    continue

                if self.on_progress is not None:
                    self.on_progress(
                        index,
                        total,
                        f"{image_path.name} -> {emoji_name}",
                    )

                try:
                    self._upload_one(driver, wait, add_url, image_path, emoji_name)
                    success += 1
                    time.sleep(self.config.pause)
                except Exception as error:  # noqa: BLE001
                    failed.append((image_path, str(error)))
        finally:
            driver.quit()

        return UploadResult(success=success, failed=failed)

    def _login(self, driver, wait, add_url: str) -> None:
        """로그인 방식을 분기한다."""
        default_login_mode = (
            self.app_config.mattermost_login_mode
            if self.app_config is not None
            else "manual"
        )
        login_mode = self.config.login_mode or default_login_mode

        if login_mode == "manual":
            self._manual_login(driver, wait, add_url)
            return

        if login_mode == "auto":
            self._auto_login(driver, wait, add_url)
            return

        raise ValueError(f"지원하지 않는 로그인 방식입니다: {login_mode}")

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
        options.add_argument(f"--window-size={self.config.driver.window_size}")
        if self.config.driver.disable_automation_control:
            options.add_argument("--disable-blink-features=AutomationControlled")

        if self.config.user_data_dir:
            options.add_argument(f"--user-data-dir={self.config.user_data_dir}")
        if self.config.profile_directory:
            options.add_argument(f"--profile-directory={self.config.profile_directory}")

        return webdriver.Chrome(options=options, service=Service())

    def _manual_login(self, driver, wait, add_url: str) -> None:
        """사용자가 직접 로그인할 수 있도록 대기한다."""
        self._open_browser_view(driver, wait, add_url)
        print("브라우저가 열렸습니다.")
        print("meeting.ssafy 로그인 상태가 아니라면 직접 로그인한 뒤 Enter를 누르세요.")
        input()
        driver.get(add_url)

    def _auto_login(self, driver, wait, add_url: str) -> None:
        """자동 로그인 진입점을 제공한다."""
        self._open_browser_view(driver, wait, add_url)
        raise NotImplementedError("자동 로그인은 아직 구현되지 않았습니다.")

    def _open_browser_view(self, driver, wait, add_url: str) -> None:
        """랜딩 페이지에서 브라우저 보기로 진입한다."""
        driver.get(add_url)

        browser_view_buttons = driver.find_elements(
            By.XPATH,
            "//a[normalize-space()='브라우저에서 보기']",
        )
        if not browser_view_buttons:
            return

        browser_view_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='브라우저에서 보기']")
            )
        )
        browser_view_button.click()

    def _open_add_page(self, driver, wait, add_url: str) -> None:
        """이모지 업로드 페이지를 연다."""
        driver.get(add_url)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.config.page.name_input_selector)
            )
        )
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.config.page.file_input_selector)
            )
        )

    def _upload_one(
        self, driver, wait, add_url: str, image_path, emoji_name: str
    ) -> None:
        """이미지 하나를 업로드한다."""
        self._open_add_page(driver, wait, add_url)

        name_input = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, self.config.page.name_input_selector)
            )
        )
        file_input = driver.find_element(
            By.CSS_SELECTOR,
            self.config.page.file_input_selector,
        )
        save_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, self.config.page.save_button_xpath))
        )

        name_input.clear()
        name_input.send_keys(emoji_name)
        file_input.send_keys(str(image_path.resolve()))
        save_button.click()

        try:
            wait.until(
                lambda current_driver: (
                    current_driver.current_url != add_url
                    or not current_driver.find_elements(
                        By.CSS_SELECTOR,
                        self.config.page.name_input_selector,
                    )
                )
            )
        except TimeoutException:
            alerts = driver.find_elements(
                By.CSS_SELECTOR,
                self.config.page.alert_selector,
            )
            messages = [alert.text.strip() for alert in alerts if alert.text.strip()]
            joined = (
                " | ".join(messages) if messages else "저장 후 페이지 변화가 없습니다."
            )
            raise RuntimeError(joined)
