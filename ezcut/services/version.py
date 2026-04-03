import datetime
import json
from pathlib import Path
from typing import Optional

import requests
from packaging import version

from ezcut import __version__


class VersionService:
    """앱 버전 관리 및 업데이트 체크 서비스."""

    REPO_URL = "https://api.github.com/repos/S-P-A-N/ezcut-gif/releases/latest"
    CACHE_DIR = Path.home() / ".config" / "ezcut"
    CACHE_FILE = CACHE_DIR / "update_cache.json"
    CACHE_TTL = datetime.timedelta(hours=24)

    def __init__(self):
        self._current_version = __version__
        self._latest_version = None

    def get_current_version(self) -> str:
        """현재 설치된 패키지의 버전을 반환합니다."""
        return self._current_version

    def get_latest_version(self, force: bool = False) -> Optional[str]:
        """GitHub API를 통해 최신 릴리스 버전을 가져옵니다 (캐시 지원)."""
        if not force and self._latest_version:
            return self._latest_version

        # 1. 캐시 확인
        if not force and self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                last_checked = datetime.datetime.fromisoformat(cache["last_checked"])
                if datetime.datetime.now() - last_checked < self.CACHE_TTL:
                    self._latest_version = cache["latest_version"]
                    return self._latest_version
            except Exception:
                pass  # 캐시 읽기 실패 시 무시하고 새로 요청

        # 2. GitHub API 요청
        try:
            response = requests.get(self.REPO_URL, timeout=2.0)
            response.raise_for_status()
            data = response.json()
            tag_name = data.get("tag_name", "")
            latest = tag_name.lstrip("v")
            self._latest_version = latest

            # 3. 캐시 저장
            try:
                self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "latest_version": latest,
                            "last_checked": datetime.datetime.now().isoformat(),
                        },
                        f,
                    )
            except Exception:
                pass

            return self._latest_version
        except Exception:
            return None

    def check_update(self) -> tuple[bool, Optional[str]]:
        """업데이트가 필요한지 확인합니다. (is_available, latest_version)"""
        latest_str = self.get_latest_version()
        if not latest_str:
            return False, None

        try:
            current_v = version.parse(self._current_version)
            latest_v = version.parse(latest_str)
            return latest_v > current_v, latest_str
        except Exception:
            # 파싱 실패 시 문자열 비교로 대체
            return self._current_version != latest_str, latest_str
