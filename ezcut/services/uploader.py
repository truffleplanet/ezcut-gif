import time
from collections.abc import Callable
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

BROWSER_VIEW_XPATH = "//a[normalize-space()='브라우저에서 보기']"
LOGIN_EMAIL_SELECTOR = "input#input_loginId"
LOGIN_PASSWORD_SELECTOR = "input#input_password-input"
LOGIN_SUBMIT_SELECTOR = "button#saveSetting"


class Uploader:
    """Mattermost 업로드 상태를 관리하는 서비스."""

    def __init__(
        self,
        config: UploadConfig,
        app_config: AppConfig | None = None,
        credentials: CredentialRepository | None = None,
        on_progress: ProgressCallback | None = None,
        wait_for_manual_login: Callable[[], None] | None = None,
    ) -> None:
        self.config = config
        self.app_config = app_config
        self.credentials = credentials
        self.on_progress = on_progress
        self.wait_for_manual_login = wait_for_manual_login
        self.files: list = []

    def run(self) -> UploadResult:
        """업로드 작업을 실행하고 결과를 반환한다."""
        self.files = list_image_files(self.config.directory)
        self.files = self.files[self.config.start_index - 1 :]
        limit_applied = False
        if self.config.limit is not None:
            if len(self.files) > self.config.limit:
                limit_applied = True
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
            success_indices: list[int] = []

            for i, image_path in enumerate(self.files):
                current_index = self.config.start_index + i  # 1-based index
                emoji_name = normalize_emoji_name(
                    image_path.stem,
                    self.config.name_prefix,
                )

                if not emoji_name:
                    failed.append((image_path, "이모지 이름이 비어 있습니다."))
                    continue

                if self.on_progress is not None:
                    self.on_progress(
                        i + 1,
                        total,
                        f"{image_path.name} -> {emoji_name}",
                    )

                try:
                    self._upload_one(driver, wait, add_url, image_path, emoji_name)
                    success += 1
                    success_indices.append(current_index)
                    time.sleep(self.config.pause)
                except Exception as error:  # noqa: BLE001
                    failed.append((image_path, str(error)))
        finally:
            driver.quit()

        return UploadResult(
            success=success,
            failed=failed,
            reached_end=not limit_applied,
            success_indices=success_indices,
        )

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
        if self.wait_for_manual_login is not None:
            self.wait_for_manual_login()
        else:
            print("브라우저가 열렸습니다.")
            print(
                "meeting.ssafy 로그인 상태가 아니라면 직접 로그인한 뒤 Enter를 누르세요."
            )
            input()
        self._wait_until_add_page(driver, wait)

    def _auto_login(self, driver, wait, add_url: str) -> None:
        """저장된 자격 증명으로 자동 로그인을 시도한다."""
        email = self._resolve_login_email()
        password = self._resolve_login_password(email)

        self._open_browser_view(driver, wait, add_url)

        if self._is_add_page_ready(driver):
            return

        self._wait_until_login_form(wait)

        email_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, LOGIN_EMAIL_SELECTOR))
        )
        password_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, LOGIN_PASSWORD_SELECTOR))
        )
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, LOGIN_SUBMIT_SELECTOR))
        )

        email_input.clear()
        email_input.send_keys(email)
        password_input.clear()
        password_input.send_keys(password)
        submit_button.click()

        self._wait_until_add_page(driver, wait)

    def _open_browser_view(self, driver, wait, add_url: str) -> None:
        """랜딩 페이지에서 브라우저 보기로 진입한다."""
        driver.get(add_url)

        page_state = self._wait_for_page_state(wait)
        if page_state in {"add", "login"}:
            return

        browser_view_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, BROWSER_VIEW_XPATH))
        )
        browser_view_button.click()
        self._wait_for_page_state(wait)

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

    def _resolve_login_email(self) -> str:
        """자동 로그인에 사용할 이메일을 반환한다."""
        if self.app_config is None or not self.app_config.mattermost_email.strip():
            raise ValueError("저장된 Mattermost 이메일이 없습니다.")

        return self.app_config.mattermost_email.strip()

    def _resolve_login_password(self, email: str) -> str:
        """자동 로그인에 사용할 비밀번호를 반환한다."""
        if self.credentials is None:
            raise ValueError("자격 증명 저장소가 연결되지 않았습니다.")

        password = self.credentials.get_password(email)
        if not password:
            raise ValueError("저장된 Mattermost 비밀번호가 없습니다.")

        return password

    def _wait_until_login_form(self, wait) -> None:
        """로그인 폼이 나타날 때까지 대기한다."""
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_EMAIL_SELECTOR))
            )
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, LOGIN_PASSWORD_SELECTOR)
                )
            )
        except TimeoutException as error:
            raise RuntimeError("Mattermost 로그인 폼을 찾지 못했습니다.") from error

    def _wait_until_add_page(self, driver, wait) -> None:
        """업로드 페이지가 열릴 때까지 대기한다."""
        try:
            wait.until(lambda current_driver: self._is_add_page_ready(current_driver))
        except TimeoutException as error:
            raise RuntimeError("이모지 업로드 페이지로 진입하지 못했습니다.") from error

    def _is_add_page_ready(self, driver) -> bool:
        """이모지 업로드 폼이 준비됐는지 확인한다."""
        return bool(
            driver.find_elements(By.CSS_SELECTOR, self.config.page.name_input_selector)
        ) and bool(
            driver.find_elements(By.CSS_SELECTOR, self.config.page.file_input_selector)
        )

    def _wait_for_page_state(self, wait) -> str:
        """현재 페이지 상태를 판별한다."""
        try:
            return wait.until(
                lambda driver: (
                    "add"
                    if self._is_add_page_ready(driver)
                    else "login"
                    if driver.find_elements(By.CSS_SELECTOR, LOGIN_EMAIL_SELECTOR)
                    and driver.find_elements(By.CSS_SELECTOR, LOGIN_PASSWORD_SELECTOR)
                    else "browser_view"
                    if driver.find_elements(By.XPATH, BROWSER_VIEW_XPATH)
                    else False
                )
            )
        except TimeoutException as error:
            raise RuntimeError(
                "Mattermost 로그인 페이지 또는 업로드 페이지를 찾지 못했습니다."
            ) from error
