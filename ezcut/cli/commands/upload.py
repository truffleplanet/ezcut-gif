"""ezcut upload 커맨드.

Phase 1에서는 manual login 기준으로 구현한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from ...repository.config import ConfigRepository
from ...repository.history import HistoryRepository
from ...services.uploader import Uploader
from ...store.models import UploadConfig
from ..prompts import (
    ask_confirm,
    ask_directory,
    ask_float,
    ask_int,
    step_header,
)
from ..render import (
    console,
    make_progress,
    make_progress_callback,
    print_dim,
    print_error,
    render_upload_result,
)


def upload_cmd(
    directory: Annotated[
        Optional[Path],
        typer.Argument(
            help="업로드할 이미지 디렉토리",
            show_default=False,
        ),
    ] = None,
    last: Annotated[
        bool,
        typer.Option("--last", help="가장 최근 split 결과를 업로드"),
    ] = False,
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-l", help="업로드할 파일 수 제한"),
    ] = None,
    start_index: Annotated[
        int,
        typer.Option("--start-index", help="시작 인덱스 (1부터)"),
    ] = 1,
    pause: Annotated[
        float,
        typer.Option("--pause", help="업로드 간 대기 시간 (초)"),
    ] = 0.3,
    headless: Annotated[
        bool,
        typer.Option("--headless", help="헤드리스 모드"),
    ] = False,
    base_url: Annotated[
        Optional[str],
        typer.Option("--base-url", help="Mattermost 서버 URL"),
    ] = None,
    add_path: Annotated[
        Optional[str],
        typer.Option("--add-path", help="이모지 추가 경로"),
    ] = None,
    name_prefix: Annotated[
        str,
        typer.Option("--name-prefix", help="이모지 이름 접두어"),
    ] = "",
) -> None:
    """Mattermost에 이모지를 업로드한다."""
    # --last 플래그 처리
    if last:
        directory = _resolve_last()

    interactive = directory is None

    if interactive:
        directory, limit, start_index, pause = _wizard()

    assert directory is not None  # noqa: S101

    app_config = ConfigRepository().load()

    config = UploadConfig(
        directory=directory,
        base_url=base_url or app_config.mattermost_base_url,
        add_path=add_path or app_config.mattermost_add_path,
        pause=pause,
        headless=headless,
        start_index=start_index,
        limit=limit,
        name_prefix=name_prefix,
        login_mode="manual",
    )

    console.print()
    print_dim(f"Directory: {directory}")
    print_dim(f"Target: {config.base_url}/{config.add_path}")

    with make_progress() as progress:
        task = progress.add_task("Uploading...", total=None)
        callback = make_progress_callback(progress, task)
        uploader = Uploader(config, app_config=app_config, on_progress=callback)

        try:
            result = uploader.run()
        except (ValueError, RuntimeError) as exc:
            progress.stop()
            print_error(str(exc))
            raise typer.Exit(1) from exc

    console.print()
    render_upload_result(result)


def _resolve_last() -> Path:
    """최근 히스토리에서 출력 디렉토리를 가져온다."""
    latest = HistoryRepository().latest()
    if latest is None:
        print_error("히스토리가 비어 있습니다. 먼저 split을 실행해주세요.")
        raise typer.Exit(1)
    path = Path(latest.output_dir)
    if not path.is_dir():
        print_error(f"디렉토리를 찾을 수 없습니다: {path}")
        raise typer.Exit(1)
    print_dim(f"Using latest: {latest.emoji_name} ({path})")
    return path


def _wizard() -> tuple[Path, int | None, int, float]:
    """인터랙티브 위자드로 upload 설정을 수집한다."""
    total_steps = 3
    history = HistoryRepository()
    latest = history.latest()

    step_header(1, total_steps, "업로드 대상")
    if latest:
        use_latest = ask_confirm(
            f"최근 작업 사용? ({latest.emoji_name}, {latest.output_dir})",
            default=True,
        )
        if use_latest:
            directory = Path(latest.output_dir)
        else:
            directory = ask_directory("이미지 디렉토리", must_exist=True)
    else:
        directory = ask_directory("이미지 디렉토리", must_exist=True)

    step_header(2, total_steps, "업로드 범위")
    si = ask_int("시작 인덱스", default=1, hint="1부터")
    assert si is not None  # noqa: S101
    lim = ask_int("업로드 개수 제한", hint="Enter=전체")

    step_header(3, total_steps, "업로드 설정")
    p = ask_float("업로드 간 대기 (초)", default=0.3)
    assert p is not None  # noqa: S101

    return directory, lim, si, p
