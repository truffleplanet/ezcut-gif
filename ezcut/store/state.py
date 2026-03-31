from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ezcut.store.models import SplitResult

ProgressCallback = Callable[[int, int, str], None]
"""(현재값, 전체값, 메시지) 시그니처의 진행률 콜백."""


@dataclass
class SplitFormState:
    """Split 탭 입력 상태."""

    input_path: Path | None = None
    output_dir: Path | None = None
    cols: int | None = None
    rows: int | None = None
    emoji_name: str = ""
    tile_size: int = 128
    max_file_size_kb: int = 512


@dataclass
class SplitTaskState:
    """Split 작업 상태."""

    is_running: bool = False
    current: int = 0
    total: int = 0
    message: str = ""
    last_result: SplitResult | None = None
    error_message: str = ""


@dataclass
class PreviewTaskState:
    """Preview 작업 상태."""

    is_loaded: bool = False
    is_playing: bool = False
    timeline_ms: int = 0
    selected_directory: Path | None = None
    error_message: str = ""


@dataclass
class UploadFormState:
    """Upload 탭 입력 상태."""

    directory: Path | None = None
    base_url: str = "https://meeting.ssafy.com"
    add_path: str = "s14public/emoji/add"
    pause: float = 0.3
    headless: bool = False
    start_index: int = 1
    limit: int | None = None
    name_prefix: str = ""
    login_mode: str = "manual"  # manual | auto


@dataclass
class UploadTaskState:
    """Upload 작업 상태."""

    is_running: bool = False
    current: int = 0
    total: int = 0
    message: str = ""
    success: int = 0
    failed: list[tuple[Path, str]] = field(default_factory=list)
    error_message: str = ""
