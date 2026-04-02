"""Cloudflare 프록시 기반 갤러리 공유 서비스.

ezcut-proxy Worker를 통해 galley 레포에
원본 GIF, emoji.txt, 메타데이터를 업로드한다.

Worker는 GitHub Contents API의 투명 프록시다:
  클라이언트 X-API-Key → Worker 검증 → Authorization: Bearer {GITHUB_PAT} 주입 → GitHub API 전달
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from ezcut.store.constants import GALLERY_API_BASE, GALLERY_API_KEY, GALLERY_PAGES_BASE
from ezcut.store.models import GalleryConfig, ShareResult
from ezcut.store.state import ProgressCallback


class GalleryService:
    """갤러리에 이모지 세트를 공유하는 서비스."""

    def __init__(
        self,
        config: GalleryConfig,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self._on_progress = on_progress
        self._owner, self._repo = config.gallery_repo.split("/", 1)
        self._session = self._build_session()

    def run(self) -> ShareResult:
        """갤러리에 이모지 세트를 업로드한다."""
        config = self.config

        # 1. 입력 검증
        if not Path(config.input_path).is_file():
            return ShareResult(
                success=False,
                error_message=f"원본 GIF 파일을 찾을 수 없습니다: {config.input_path}",
            )

        emoji_txt_path = Path(config.output_dir) / "emoji.txt"
        if not emoji_txt_path.is_file():
            return ShareResult(
                success=False,
                error_message=f"emoji.txt를 찾을 수 없습니다: {emoji_txt_path}",
            )

        # 2. gallery.json 읽기 + 중복 검사
        self._report(1, 5, "갤러리 인덱스 확인 중...")
        gallery_data, gallery_sha = self._get_gallery_index()
        emoji_name = self._resolve_unique_name(gallery_data, config.emoji_name)

        # 3. 원본 GIF 업로드
        self._report(2, 5, "원본 GIF 업로드 중...")
        gif_bytes = Path(config.input_path).read_bytes()
        self._put_file(
            f"emojis/{emoji_name}/original.gif",
            gif_bytes,
            f"add: {emoji_name} original.gif",
        )

        # 4. emoji.txt 업로드
        self._report(3, 5, "emoji.txt 업로드 중...")
        emoji_txt_bytes = emoji_txt_path.read_bytes()
        self._put_file(
            f"emojis/{emoji_name}/emoji.txt",
            emoji_txt_bytes,
            f"add: {emoji_name} emoji.txt",
        )

        # 5. metadata.json 업로드
        self._report(4, 5, "메타데이터 업로드 중...")
        metadata = self._build_metadata(emoji_name)
        metadata_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode()
        self._put_file(
            f"emojis/{emoji_name}/metadata.json",
            metadata_bytes,
            f"add: {emoji_name} metadata.json",
        )

        # 6. gallery.json 업데이트
        self._report(5, 5, "갤러리 인덱스 업데이트 중...")
        gallery_data.insert(0, metadata)
        self._update_gallery_index(gallery_data, gallery_sha)

        gallery_url = (
            f"{GALLERY_PAGES_BASE.format(owner=self._owner, repo=self._repo)}"
            f"#{emoji_name}"
        )

        return ShareResult(
            success=True,
            gallery_url=gallery_url,
            emoji_name=emoji_name,
        )

    # ── 프록시 API 헬퍼 ──────────────────────────────────────

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "X-API-Key": GALLERY_API_KEY,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        return session

    def _api_url(self, path: str) -> str:
        return f"{GALLERY_API_BASE}/repos/{self._owner}/{self._repo}/contents/{path}"

    def _get_file(self, path: str) -> tuple[bytes, str]:
        """파일 내용과 SHA를 가져온다."""
        try:
            resp = self._session.get(self._api_url(path), timeout=30)
        except requests.exceptions.ConnectionError as exc:
            raise GalleryAPIError(
                "갤러리 서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise GalleryAPIError(
                "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            ) from exc
        self._check_response(resp)
        data = resp.json()
        content = base64.b64decode(data["content"])
        return content, data["sha"]

    def _put_file(
        self,
        path: str,
        content: bytes,
        message: str,
        sha: str | None = None,
    ) -> None:
        """파일을 생성하거나 업데이트한다."""
        payload: dict = {
            "message": message,
            "content": base64.b64encode(content).decode(),
        }
        if sha:
            payload["sha"] = sha

        try:
            resp = self._session.put(self._api_url(path), json=payload, timeout=60)
        except requests.exceptions.ConnectionError as exc:
            raise GalleryAPIError(
                "갤러리 서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise GalleryAPIError(
                "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            ) from exc
        self._check_response(resp)

    def _get_gallery_index(self) -> tuple[list[dict], str]:
        """gallery.json을 읽어 목록과 SHA를 반환한다."""
        try:
            content, sha = self._get_file("gallery.json")
            return json.loads(content), sha
        except GalleryAPIError as exc:
            if exc.status_code == 404:
                return [], ""
            raise

    def _update_gallery_index(self, gallery_data: list[dict], sha: str) -> None:
        """gallery.json을 원자적으로 업데이트한다. SHA 충돌 시 1회 재시도."""
        content = json.dumps(gallery_data, ensure_ascii=False, indent=2).encode()
        try:
            self._put_file(
                "gallery.json",
                content,
                f"update: gallery index ({len(gallery_data)} entries)",
                sha or None,
            )
        except GalleryAPIError as exc:
            if exc.status_code != 409:
                raise
            # SHA 충돌 — 재시도
            current_data, current_sha = self._get_gallery_index()
            entry = gallery_data[0]
            current_data.insert(0, entry)
            retry_content = json.dumps(
                current_data, ensure_ascii=False, indent=2
            ).encode()
            self._put_file(
                "gallery.json",
                retry_content,
                f"update: gallery index ({len(current_data)} entries)",
                current_sha or None,
            )

    def _check_response(self, resp: requests.Response) -> None:
        if resp.ok:
            return

        status = resp.status_code
        messages = {
            401: "API 키가 유효하지 않습니다. 앱을 최신 버전으로 업데이트해주세요.",
            403: (
                "갤러리 서비스가 일시적으로 제한 중입니다. 잠시 후 다시 시도해주세요.\n"
                f"  (경로: {resp.request.url if resp.request else '?'})"
            ),
            404: f"갤러리 레포를 찾을 수 없습니다: {self.config.gallery_repo}",
            409: "파일 충돌이 발생했습니다.",
            413: "파일 크기가 너무 큽니다. --max-size 옵션으로 타일 크기를 줄여보세요.",
            429: "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        }
        if status >= 500:
            message = (
                f"갤러리 서버 오류({status})가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        else:
            message = messages.get(
                status, f"갤러리 API 오류 ({status}): {resp.text[:200]}"
            )
        raise GalleryAPIError(message, status_code=status)

    # ── 유틸 ─────────────────────────────────────────────────

    @staticmethod
    def _resolve_unique_name(gallery_data: list[dict], emoji_name: str) -> str:
        """갤러리 내 중복되지 않는 이름을 반환한다."""
        existing = {entry["name"] for entry in gallery_data}
        if emoji_name not in existing:
            return emoji_name

        for suffix in range(2, 100):
            candidate = f"{emoji_name}-{suffix}"
            if candidate not in existing:
                return candidate

        return f"{emoji_name}-{len(existing)}"

    def _build_metadata(self, emoji_name: str) -> dict:
        config = self.config
        return {
            "name": emoji_name,
            "cols": config.cols,
            "rows": config.rows,
            "tile_size": config.tile_size,
            "frame_step": config.frame_step,
            "tile_count": config.tile_count,
            "author": config.author,
            "shared_at": datetime.now(timezone.utc).isoformat(),
            "original_gif": f"emojis/{emoji_name}/original.gif",
            "emoji_txt": f"emojis/{emoji_name}/emoji.txt",
        }

    def _report(self, current: int, total: int, message: str) -> None:
        if self._on_progress:
            self._on_progress(current, total, message)


class GalleryAPIError(Exception):
    """갤러리 API 호출 실패."""

    def __init__(self, message: str, *, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code
