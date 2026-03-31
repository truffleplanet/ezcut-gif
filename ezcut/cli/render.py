"""Rich 기반 렌더링 헬퍼.

배너, 패널, 테이블, 프로그레스 바 등 CLI 전체에서 재사용하는 출력 요소를 제공한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..repository.history import HistoryEntry
    from ..store.models import SplitResult, UploadResult
    from ..store.state import ProgressCallback

# ── 공용 콘솔 ─────────────────────────────────────────────
console = Console()

# ── 색상 팔레트 (미쿠 테마) ───────────────────────────────
ACCENT = "cyan"
DIM = "dim"
SUCCESS = "green"
ERROR = "bold red"
WARN = "yellow"
LABEL = "bold cyan"
VALUE = "white"

# ── 에셋 경로 ─────────────────────────────────────────────
_ASSETS_DIR = Path(__file__).parent / "assets"


def _load_asset(name: str) -> str:
    path = _ASSETS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip("\n")
    return ""


# ── 배너 ──────────────────────────────────────────────────


def render_banner() -> None:
    """미쿠 ASCII art + 타이틀을 출력한다."""
    art = _load_asset("miku_filled.txt")
    if art:
        console.print(Text(art, style=ACCENT))
    console.print()
    console.print(
        Text("  ezcut", style="bold cyan")
        + Text(" \u2014 GIF grid splitter & Mattermost uploader", style=DIM),
    )
    console.print()


# ── 상태 요약 패널 ────────────────────────────────────────


def render_home_status(
    latest: HistoryEntry | None,
    commands: list[tuple[str, str]],
) -> None:
    """홈 화면 상태 요약을 패널로 출력한다."""
    lines: list[str] = []

    if latest:
        lines.append(
            f"[{LABEL}]Latest[/]  "
            f"[{VALUE}]{latest.emoji_name}[/] "
            f"[{DIM}]({latest.cols}x{latest.rows}, "
            f"step={latest.frame_step})[/]"
        )
        lines.append(f"[{DIM}]         {latest.output_dir}[/]")
    else:
        lines.append(f"[{DIM}]No recent work.[/]")

    panel = Panel(
        "\n".join(lines),
        border_style=ACCENT,
        padding=(0, 1),
    )
    console.print(panel)

    # 커맨드 안내
    for key, desc in commands:
        console.print(f"  [{ACCENT}]{key}[/]  {desc}")
    console.print()


# ── Split 결과 ────────────────────────────────────────────


def render_split_summary(result: SplitResult) -> None:
    """split 완료 후 결과 요약을 출력한다."""
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        expand=False,
    )
    table.add_column(style=LABEL, no_wrap=True)
    table.add_column(style=VALUE)

    table.add_row("Output", str(result.output_dir))
    table.add_row("Grid", f"{result.cols} x {result.rows}")
    table.add_row("Tiles", str(len(result.filenames)))
    table.add_row("Frame step", str(result.frame_step))
    table.add_row("emoji.txt", str(result.emoji_txt_path))

    panel = Panel(
        table,
        title="[bold green]Split complete[/]",
        border_style=SUCCESS,
        padding=(1, 1),
    )
    console.print(panel)


# ── History 테이블 ────────────────────────────────────────


def render_history_table(entries: list[HistoryEntry]) -> None:
    """히스토리 목록을 테이블로 출력한다."""
    if not entries:
        console.print(f"  [{DIM}]No history yet.[/]")
        return

    table = Table(box=None, padding=(0, 1), expand=False)
    table.add_column("#", style=DIM, justify="right")
    table.add_column("Name", style=ACCENT)
    table.add_column("Grid", style=VALUE)
    table.add_column("Step", style=VALUE, justify="right")
    table.add_column("Date", style=DIM)
    table.add_column("Output", style=DIM)

    for idx, entry in enumerate(entries, start=1):
        date_part = (
            entry.timestamp[:10] if len(entry.timestamp) >= 10 else entry.timestamp
        )
        table.add_row(
            str(idx),
            entry.emoji_name,
            f"{entry.cols}x{entry.rows}",
            str(entry.frame_step),
            date_part,
            entry.output_dir,
        )

    console.print(table)


def render_history_latest(entry: HistoryEntry) -> None:
    """최신 히스토리 1건을 패널로 출력한다."""
    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column(style=LABEL, no_wrap=True)
    table.add_column(style=VALUE)

    table.add_row("Name", entry.emoji_name)
    table.add_row("Grid", f"{entry.cols}x{entry.rows}")
    table.add_row("Tile size", str(entry.tile_size))
    table.add_row("Frame step", str(entry.frame_step))
    table.add_row("Tiles", str(entry.tile_count))
    table.add_row("Input", entry.input_path)
    table.add_row("Output", entry.output_dir)
    table.add_row("Date", entry.timestamp)

    panel = Panel(
        table, title="[bold cyan]Latest[/]", border_style=ACCENT, padding=(1, 1)
    )
    console.print(panel)


# ── Upload 결과 ───────────────────────────────────────────


def render_upload_result(result: UploadResult) -> None:
    """업로드 결과를 출력한다."""
    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column(style=LABEL, no_wrap=True)
    table.add_column(style=VALUE)

    table.add_row("Success", f"[{SUCCESS}]{result.success}[/]")
    table.add_row(
        "Failed", f"[{ERROR}]{len(result.failed)}[/]" if result.failed else "0"
    )

    panel = Panel(
        table,
        title="[bold green]Upload complete[/]"
        if not result.failed
        else "[bold yellow]Upload finished[/]",
        border_style=SUCCESS if not result.failed else WARN,
        padding=(1, 1),
    )
    console.print(panel)

    if result.failed:
        console.print()
        console.print(f"  [{ERROR}]Failed files:[/]")
        for path, reason in result.failed:
            console.print(f"    [{DIM}]{path.name}[/]  {reason}")


# ── 프로그레스 바 ─────────────────────────────────────────


def make_progress() -> Progress:
    """공용 Rich Progress 인스턴스를 생성한다."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def make_progress_callback(progress: Progress, task_id: int) -> ProgressCallback:
    """서비스 계층에 넘길 ProgressCallback을 생성한다."""

    def _callback(current: int, total: int, message: str) -> None:
        progress.update(task_id, completed=current, total=total, description=message)

    return _callback


# ── 유틸 ──────────────────────────────────────────────────


def print_error(message: str) -> None:
    console.print(f"  [{ERROR}]Error:[/] {message}")


def print_success(message: str) -> None:
    console.print(f"  [{SUCCESS}]{message}[/]")


def print_dim(message: str) -> None:
    console.print(f"  [{DIM}]{message}[/]")
