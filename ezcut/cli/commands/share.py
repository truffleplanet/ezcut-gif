from pathlib import Path
from typing import Annotated, Optional

import typer

from ezcut.cli.prompts import ask_confirm, prompt_history_selection
from ezcut.cli.render import (
    console,
    make_progress,
    make_progress_callback,
    print_error,
    render_share_result,
)
from ezcut.services.config import ConfigService
from ezcut.services.exceptions import HistoryNotFoundError
from ezcut.services.gallery import GalleryAPIError, GalleryService
from ezcut.services.history import HistoryEntry, HistoryService
from ezcut.store.models import GalleryConfig


def share_cmd(
    directory: Annotated[
        Optional[Path],
        typer.Argument(
            help="공유할 이모지 디렉토리",
            show_default=False,
        ),
    ] = None,
    last: Annotated[
        bool,
        typer.Option("--last", help="가장 최근 split 결과를 공유"),
    ] = False,
) -> None:
    """갤러리에 이모지 세트를 공유한다."""
    history_service = HistoryService()

    try:
        if directory is not None and not last:
            entry = history_service.resolve_from_directory(directory)
        elif last:
            entry = history_service.get_latest()
            if entry is None:
                raise HistoryNotFoundError(
                    "히스토리가 비어 있습니다. 먼저 split을 실행해주세요."
                )
        else:
            entries = history_service.list_history(limit=20)
            if not entries:
                raise HistoryNotFoundError(
                    "히스토리가 비어 있습니다. 먼저 split을 실행해주세요."
                )
            selected = prompt_history_selection(entries)
            if selected is None:
                raise typer.Exit()
            entry = selected
    except HistoryNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc

    _run_gallery_share(entry, history_service)


def _run_gallery_share(entry: HistoryEntry, history_service: HistoryService) -> None:
    """갤러리 공유를 실행한다."""
    if not entry.uploaded:
        print_error(
            "먼저 Mattermost에 업로드한 후 공유해주세요.\n  ezcut upload --last"
        )
        return

    if entry.gallery_name:
        print_error(
            f"이미 갤러리에 공유된 이모지입니다. (갤러리 이름: {entry.gallery_name})"
        )
        return

    config_service = ConfigService()

    config = GalleryConfig(
        gallery_repo=config_service.load_config().gallery_repo,
        emoji_name=entry.emoji_name,
        input_path=Path(entry.input_path),
        output_dir=Path(entry.output_dir),
        cols=entry.cols,
        rows=entry.rows,
        tile_size=entry.tile_size,
        frame_step=entry.frame_step,
        tile_count=entry.tile_count,
    )

    with make_progress() as progress:
        task = progress.add_task("Sharing...", total=None)
        callback = make_progress_callback(progress, task)
        service = GalleryService(config, on_progress=callback)

        try:
            result = service.run()
        except GalleryAPIError as exc:
            progress.stop()
            print_error(str(exc))
            return

    if result.success:
        history_service.mark_shared(entry, result.emoji_name)

    console.print()
    render_share_result(result)


def offer_gallery_share(entry: HistoryEntry | None = None) -> None:
    """업로드 성공 후 갤러리 공유를 제안한다. upload 커맨드에서 호출."""
    try:
        share = ask_confirm("갤러리에 공유할까요?", default=False)
    except KeyboardInterrupt:
        return

    if not share:
        return

    history_service = HistoryService()
    if entry is None:
        entry = history_service.get_latest()

    if entry is None:
        print_error("히스토리가 비어 있습니다.")
        return

    _run_gallery_share(entry, history_service)
