from pathlib import Path
from typing import Annotated, Optional

import typer

from ezcut.cli.prompts import (
    ask_int,
    prompt_emoji_name,
    prompt_input_path,
    prompt_output_dir,
    step_header,
)
from ezcut.cli.render import (
    console,
    make_progress,
    make_progress_callback,
    print_error,
    render_split_summary,
)
from ezcut.services.history import HistoryService
from ezcut.services.split_workflow import SplitWorkflow
from ezcut.services.splitter import Splitter
from ezcut.store.models import SplitConfig


def split_cmd(
    input_path: Annotated[
        Optional[Path],
        typer.Argument(
            help="분할할 GIF 파일 경로",
            show_default=False,
        ),
    ] = None,
    cols: Annotated[
        Optional[int],
        typer.Option("--cols", "-c", help="가로 조각 수"),
    ] = None,
    rows: Annotated[
        Optional[int],
        typer.Option("--rows", "-r", help="세로 조각 수"),
    ] = None,
    size: Annotated[
        int,
        typer.Option("--size", "-s", help="타일 크기 (px)"),
    ] = 128,
    max_size: Annotated[
        int,
        typer.Option("--max-size", help="타일 최대 파일 크기 (KB)"),
    ] = 512,
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output-dir", "-o", help="출력 디렉토리"),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="이모지 베이스 이름"),
    ] = None,
    speed: Annotated[
        float,
        typer.Option("--speed", help="배속 (1.0 = 원본)"),
    ] = 1.0,
) -> None:
    """GIF를 그리드 타일로 분할한다."""
    interactive = input_path is None

    if interactive:
        input_path, cols, rows, name, output_dir = _wizard(size)

    assert input_path is not None  # noqa: S101

    config = SplitConfig(
        input_path=input_path,
        tile_size=size,
        output_dir=output_dir,
        cols=cols,
        rows=rows,
        emoji_name=name,
        max_file_size_kb=max_size,
        speed_multiplier=speed,
    )

    history_service = HistoryService()

    console.print()
    with make_progress() as progress:
        task = progress.add_task("Preparing...", total=None)
        callback = make_progress_callback(progress, task)
        workflow = SplitWorkflow(
            config, history_service=history_service, on_progress=callback
        )

        try:
            result = workflow.run()
        except (FileNotFoundError, ValueError) as exc:
            progress.stop()
            print_error(str(exc))
            raise typer.Exit(1) from exc

    console.print()
    render_split_summary(result)


def _wizard(
    default_size: int,
) -> tuple[Path, int | None, int | None, str, Path | None]:
    """인터랙티브 위자드로 split 설정을 수집한다."""
    total_steps = 4

    step_header(1, total_steps, "GIF 파일 경로")
    path = prompt_input_path()

    step_header(2, total_steps, "그리드 설정")

    # 추천 그리드 미리 계산하여 표시
    try:
        width, height, _, _, rec_cols, rec_rows = Splitter.get_grid_recommendation(path)
        console.print(f"    [dim]원본 크기: {width} x {height}[/]")
        console.print(
            f"    [dim]추천 조각 수: "
            f"가로 [cyan]{rec_cols}[/] x 세로 [cyan]{rec_rows}[/] "
            f"(총 {rec_cols * rec_rows}개)[/]"
        )
        console.print("    [dim]Enter를 누르면 추천값을 사용합니다.[/]")
        default_cols = rec_cols
        default_rows = rec_rows
    except Exception:  # noqa: BLE001
        console.print("    [dim]Enter를 누르면 GIF 비율에 맞춰 자동 계산합니다.[/]")
        default_cols = None
        default_rows = None

    c = ask_int("가로 조각 수", default=default_cols, hint="Enter=추천값")
    r = ask_int("세로 조각 수", default=default_rows, hint="Enter=추천값")

    step_header(3, total_steps, "이모지 이름")
    emoji = prompt_emoji_name(default=path.stem)

    step_header(4, total_steps, "출력 디렉토리")
    out = prompt_output_dir(default_name=emoji or path.stem)

    return path, c, r, emoji, out
