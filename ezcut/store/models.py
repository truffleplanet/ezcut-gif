from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class SplitConfig:
    """GIF 분할 설정."""

    input_path: Path
    tile_size: int = 128
    output_dir: Path | None = None
    cols: int | None = None
    rows: int | None = None
    emoji_name: str | None = None
    max_file_size_kb: int = 512
    max_pieces: int = 144


@dataclass(frozen=True)
class SplitResult:
    """GIF 분할 결과."""

    output_dir: Path
    filenames: list[str]
    cols: int
    rows: int
    frame_step: int
    emoji_txt_path: Path


@dataclass
class Tile:
    """미리보기용 타일 상태."""

    path: Path
    row_index: int
    col_index: int
    image: Image.Image
    frame_index: int
    current_frame: Image.Image
    current_duration_ms: int
    next_change_ms: int | None


@dataclass(frozen=True)
class PreviewConfig:
    """미리보기 설정."""

    directory: Path
    scale: float | None = None
    background: str = "#000000"


@dataclass(frozen=True)
class UploadConfig:
    """Mattermost 업로드 설정."""

    directory: Path
    base_url: str = "https://meeting.ssafy.com"
    add_path: str = "s14public/emoji/add"
    pause: float = 0.3
    headless: bool = False
    start_index: int = 1
    limit: int | None = None
    name_prefix: str = ""
    user_data_dir: Path | None = None
    profile_directory: str | None = None
    login_mode: str = "auto"


@dataclass(frozen=True)
class UploadResult:
    """Mattermost 업로드 결과."""

    success: int
    failed: list[tuple[Path, str]]
