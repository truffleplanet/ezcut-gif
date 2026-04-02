import importlib.metadata
from typing import Optional

import requests


class VersionService:
    """앱 버전 관리 및 업데이트 체크 서비스."""

    REPO_URL = "https://api.github.com/repos/S-P-A-N/ezcut-gif/releases/latest"

    def __init__(self):
        self._current_version = None
        self._latest_version = None

    def get_current_version(self) -> str:
        """현재 설치된 패키지의 버전을 반환합니다."""
        if self._current_version is None:
            try:
                self._current_version = importlib.metadata.version("ezcut")
            except importlib.metadata.PackageNotFoundError:
                self._current_version = "0.0.0-dev"
        return self._current_version

    def get_latest_version(self) -> Optional[str]:
        """GitHub API를 통해 최신 릴리스 버전을 가져옵니다."""
        try:
            # 실시간 체크를 위해 타임아웃 설정 (사용자 경험 저하 방지)
            response = requests.get(self.REPO_URL, timeout=2.0)
            response.raise_for_status()
            data = response.json()
            # tag_name이 'v0.2.1' 형태일 수 있으므로 'v' 제거 처리
            tag_name = data.get("tag_name", "")
            if tag_name.startswith("v"):
                self._latest_version = tag_name[1:]
            else:
                self._latest_version = tag_name
            return self._latest_version
        except Exception:
            # 네트워크 오류, 속도 제한 등 발생 시 None 반환
            return None

    def check_update(self) -> tuple[bool, Optional[str]]:
        """업데이트가 필요한지 확인합니다. (is_available, latest_version)"""
        current = self.get_current_version()
        latest = self.get_latest_version()

        if not latest:
            return False, None

        # 단순 문자열 비교 (정밀한 비교를 원할 경우 packaging.version 사용 가능)
        if current != latest:
            return True, latest

        return False, latest
