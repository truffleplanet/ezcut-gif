from dataclasses import dataclass, field
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
    speed_multiplier: float = 1.0


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


@dataclass(frozen=True)
class AppConfig:
    """앱 기본 설정."""

    # Mattermost 기본설정
    mattermost_base_url: str = "https://meeting.ssafy.com"
    mattermost_add_path: str = "s14public/emoji/add"
    mattermost_login_mode: str = "manual"  # manual | auto
    mattermost_email: str = ""

    # Chrome 기본설정
    chrome_user_data_dir: str = ""
    chrome_profile: str = ""

    # Split 기본설정
    default_tile_size: int = 128
    default_max_file_size_kb: int = 512  # KB

    # Gallery 기본설정
    gallery_repo: str = "S-P-A-N/ezcut-gallery"


@dataclass(frozen=True)
class UploadDriverConfig:
    """업로드 드라이버 설정."""

    wait_timeout_seconds: int = 15
    window_size: str = "1600,1200"
    disable_automation_control: bool = True


@dataclass(frozen=True)
class UploadPageConfig:
    """업로드 페이지 선택자 설정."""

    name_input_selector: str = "input#name"
    file_input_selector: str = "input#select-emoji"
    save_button_xpath: str = "//button[normalize-space()='저장']"
    alert_selector: str = ".alert, .error, .has-error, .help-block"


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
    login_mode: str = "manual"  # manual | auto
    driver: UploadDriverConfig = field(default_factory=UploadDriverConfig)
    page: UploadPageConfig = field(default_factory=UploadPageConfig)


@dataclass(frozen=True)
class UploadResult:
    """Mattermost 업로드 결과."""

    success: int
    failed: list[tuple[Path, str]]
    reached_end: bool
    success_indices: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class GalleryConfig:
    """갤러리 공유 설정."""

    gallery_repo: str = "S-P-A-N/ezcut-gallery"
    emoji_name: str = ""
    input_path: Path = Path()
    output_dir: Path = Path()
    cols: int = 0
    rows: int = 0
    tile_size: int = 128
    frame_step: int = 1
    tile_count: int = 0
    author: str = ""


@dataclass(frozen=True)
class ShareResult:
    """갤러리 공유 결과."""

    success: bool
    gallery_url: str = ""
    emoji_name: str = ""
    error_message: str = ""
