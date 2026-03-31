"""Typer 루트 앱 정의.

무인자 실행 시 인터랙티브 홈 루프를, 서브커맨드 지정 시 해당 명령을 실행한다.
홈 화면은 arrow-key 메뉴로 동작하며, 커맨드 완료 후 홈으로 복귀한다.
"""

from __future__ import annotations

import typer

from ..repository.history import HistoryRepository
from .commands.history import history_cmd
from .commands.preview import preview_cmd
from .commands.split import split_cmd
from .commands.upload import upload_cmd
from .prompts import ask_select
from .render import console, render_banner, render_home_status

app = typer.Typer(
    name="ezcut",
    help="GIF를 그리드로 분할하고 Mattermost 이모지로 업로드합니다.",
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
)

# ── 서브커맨드 등록 ───────────────────────────────────────
app.command(name="split")(split_cmd)
app.command(name="preview")(preview_cmd)
app.command(name="history")(history_cmd)
app.command(name="upload")(upload_cmd)

# ── 홈 메뉴 항목 ─────────────────────────────────────────
_HOME_ACTIONS: list[tuple[str, str]] = [
    ("split", "Split   — GIF를 그리드로 분할"),
    ("preview", "Preview — 타일 미리보기"),
    ("upload", "Upload  — Mattermost에 이모지 업로드"),
    ("history", "History — 작업 히스토리 조회"),
    ("quit", "Quit"),
]

_DISPATCH = {
    "split": split_cmd,
    "preview": preview_cmd,
    "upload": upload_cmd,
    "history": history_cmd,
}


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """ezcut 홈 화면."""
    if ctx.invoked_subcommand is not None:
        return

    _home_loop(ctx)


def _home_loop(ctx: typer.Context) -> None:
    """홈 화면 루프. 커맨드 완료 후 다시 메뉴로 복귀한다."""
    first_run = True

    while True:
        if first_run:
            render_banner()
            first_run = False
        else:
            console.print()
            console.rule(style="dim")
            console.print()

        history = HistoryRepository()
        latest = history.latest()
        render_home_status(latest, [])

        try:
            choice = ask_select("무엇을 할까요?", _HOME_ACTIONS, default="split")
        except KeyboardInterrupt:
            return

        if choice == "quit":
            return

        handler = _DISPATCH.get(choice)
        if handler is None:
            return

        console.print()
        try:
            ctx.invoke(handler)
        except SystemExit:
            pass
        except KeyboardInterrupt:
            console.print("\n  [dim]Cancelled.[/]")
