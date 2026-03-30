import argparse
import re
import sys
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


VALID_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg"}
NAME_SANITIZE_RE = re.compile(r"[^a-z0-9._-]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="meeting.ssafy 커스텀 이모지를 파일명 순서대로 일괄 등록합니다."
    )
    parser.add_argument(
        "directory",
        help="업로드할 이미지들이 들어있는 폴더",
    )
    parser.add_argument(
        "--base-url",
        default="https://meeting.ssafy.com",
        help="기준 URL. 기본값: https://meeting.ssafy.com",
    )
    parser.add_argument(
        "--add-path",
        default="s14public/emoji/add",
        help="이모지 추가 페이지 상대경로 또는 전체 URL",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.3,
        help="업로드 사이 대기 시간(초). 기본값 0.3",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="헤드리스 모드로 실행",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="이 순번부터 업로드 시작. 기본값 1",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="최대 업로드 개수",
    )
    parser.add_argument(
        "--name-prefix",
        default="",
        help="이모지 이름 앞에 붙일 접두사",
    )
    parser.add_argument(
        "--user-data-dir",
        default=None,
        help="기존 크롬 로그인 세션을 재사용할 user-data-dir 경로",
    )
    parser.add_argument(
        "--profile-directory",
        default=None,
        help="크롬 프로필 디렉토리 이름. 예: Default",
    )
    return parser.parse_args()


def normalize_name(stem: str, prefix: str) -> str:
    name = f"{prefix}{stem}".lower()
    name = NAME_SANITIZE_RE.sub("-", name).strip("-")
    return name[:64]


def list_files(directory: Path) -> list[Path]:
    files = [
        path for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS
    ]
    if not files:
        raise FileNotFoundError("업로드할 gif/png/jpg 파일을 찾지 못했습니다.")
    return files


def build_driver(args: argparse.Namespace) -> webdriver.Chrome:
    options = ChromeOptions()
    if args.headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if args.user_data_dir:
        options.add_argument(f"--user-data-dir={args.user_data_dir}")
    if args.profile_directory:
        options.add_argument(f"--profile-directory={args.profile_directory}")

    return webdriver.Chrome(options=options, service=Service())


def wait_for_manual_login(driver: webdriver.Chrome, add_url: str) -> None:
    driver.get(add_url)
    print("브라우저가 열렸습니다.")
    print("meeting.ssafy 로그인 상태가 아니라면 직접 로그인한 뒤 Enter를 누르세요.")
    input()
    driver.get(add_url)


def open_add_page(driver: webdriver.Chrome, wait: WebDriverWait, add_url: str) -> None:
    driver.get(add_url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#name")))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#select-emoji")))


def upload_one(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    add_url: str,
    image_path: Path,
    emoji_name: str,
) -> None:
    open_add_page(driver, wait, add_url)

    name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#name")))
    file_input = driver.find_element(By.CSS_SELECTOR, "input#select-emoji")
    save_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='저장']"))
    )

    name_input.clear()
    name_input.send_keys(emoji_name)

    # OS 파일 선택창을 열 필요 없이 file input에 절대경로를 직접 넣으면 된다.
    file_input.send_keys(str(image_path.resolve()))
    save_button.click()

    try:
        wait.until(
            lambda d: d.current_url != add_url
            or not d.find_elements(By.CSS_SELECTOR, "input#name")
        )
    except TimeoutException:
        # 실패 메시지가 떠도 name input은 그대로 남아있을 수 있다.
        # 이 경우 상단 alert 문구를 먼저 찾아서 예외로 올린다.
        alerts = driver.find_elements(By.CSS_SELECTOR, ".alert, .error, .has-error, .help-block")
        messages = [alert.text.strip() for alert in alerts if alert.text.strip()]
        joined = " | ".join(messages) if messages else "저장 후 페이지 변화가 없습니다."
        raise RuntimeError(joined)


def main() -> int:
    args = parse_args()
    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        print(f"폴더를 찾지 못했습니다: {directory}")
        return 1

    files = list_files(directory)
    files = files[args.start_index - 1:]
    if args.limit is not None:
        files = files[:args.limit]

    if not files:
        print("조건에 맞는 업로드 대상 파일이 없습니다.")
        return 1

    if args.add_path.startswith(("http://", "https://")):
        add_url = args.add_path
    else:
        add_url = urljoin(f"{args.base_url.rstrip('/')}/", args.add_path.lstrip("/"))
    driver = build_driver(args)
    wait = WebDriverWait(driver, 15)

    success = 0
    failed: list[tuple[Path, str]] = []

    try:
        wait_for_manual_login(driver, add_url)
        for index, image_path in enumerate(files, start=1):
            emoji_name = normalize_name(image_path.stem, args.name_prefix)
            if not emoji_name:
                failed.append((image_path, "이모지 이름이 비어 있습니다."))
                continue

            print(f"[{index}/{len(files)}] {image_path.name} -> {emoji_name}")
            try:
                upload_one(driver, wait, add_url, image_path, emoji_name)
                success += 1
                time.sleep(args.pause)
            except Exception as exc:  # noqa: BLE001
                failed.append((image_path, str(exc)))
                print(f"  실패: {exc}")

    finally:
        print()
        print(f"성공: {success}")
        print(f"실패: {len(failed)}")
        for image_path, reason in failed:
            print(f"  - {image_path.name}: {reason}")
        driver.quit()

    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
