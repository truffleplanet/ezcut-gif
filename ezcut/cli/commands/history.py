from typing import Annotated

import typer

from ezcut.cli.render import render_history_latest, render_history_table
from ezcut.services.history import HistoryService


def history_cmd(
    limit: Annotated[
        int,
        typer.Option("-n", "--limit", help="표시할 항목 수"),
    ] = 10,
    latest: Annotated[
        bool,
        typer.Option("--latest", help="최신 1건만 상세 표시"),
    ] = False,
) -> None:
    """작업 히스토리를 조회한다."""
    history_service = HistoryService()

    if latest:
        entry = history_service.get_latest()
        if entry is None:
            typer.echo("  히스토리가 비어 있습니다.")
            raise typer.Exit()
        render_history_latest(entry)
    else:
        entries = history_service.list_history(limit=limit)
        render_history_table(entries)
