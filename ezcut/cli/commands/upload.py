from pathlib import Path
from typing import Annotated, Optional

import typer

from ezcut.cli.prompts import (
    ask_confirm,
    ask_directory,
    ask_float,
    ask_int,
    step_header,
)
from ezcut.cli.render import (
    console,
    make_progress,
    make_progress_callback,
    print_dim,
    print_error,
    render_upload_result,
)
from ezcut.services.config import ConfigService
from ezcut.services.history import HistoryService
from ezcut.services.uploader import Uploader
from ezcut.store.models import UploadConfig


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

    config_service = ConfigService()
    app_config = config_service.load_config()

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

    if result.success > 0:
        _mark_directory_uploaded(directory)

        from .share import offer_gallery_share

        console.print()
        offer_gallery_share()


def _mark_directory_uploaded(directory: Path) -> None:
    """업로드 성공 후 히스토리 엔트리에 uploaded 플래그를 기록한다."""
    from ezcut.services.exceptions import HistoryNotFoundError

    history_service = HistoryService()
    try:
        entry = history_service.resolve_from_directory(directory)
        history_service.mark_uploaded(entry)
    except HistoryNotFoundError:
        pass  # split 없이 직접 디렉토리를 지정한 경우 — 무시


def _resolve_last() -> Path:
    """최근 히스토리에서 출력 디렉토리를 가져온다."""
    from ezcut.services.exceptions import HistoryNotFoundError

    try:
        return HistoryService().resolve_last_path()
    except HistoryNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc


def _wizard() -> tuple[Path, int | None, int, float]:
    """인터랙티브 위자드로 upload 설정을 수집한다."""
    total_steps = 3
    history_service = HistoryService()
    latest = history_service.get_latest()

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
