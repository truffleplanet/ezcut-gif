"""ezcut history 커맨드.

작업 히스토리를 조회한다. Phase 1에서는 읽기 전용.
"""

from __future__ import annotations

from typing import Annotated

import typer

from ...repository.history import HistoryRepository
from ..render import render_history_latest, render_history_table


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
    history = HistoryRepository()

    if latest:
        entry = history.latest()
        if entry is None:
            typer.echo("  히스토리가 비어 있습니다.")
            raise typer.Exit()
        render_history_latest(entry)
    else:
        entries = history.list(limit=limit)
        render_history_table(entries)
