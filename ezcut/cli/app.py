import typer

from ezcut.cli.commands.history import history_cmd
from ezcut.cli.commands.preview import preview_cmd
from ezcut.cli.commands.share import share_cmd
from ezcut.cli.commands.split import split_cmd
from ezcut.cli.commands.upload import upload_cmd
from ezcut.cli.prompts import ask_select
from ezcut.cli.render import console, render_banner, render_home_status
from ezcut.services.history import HistoryService

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
app.command(name="share")(share_cmd)

# ── 홈 메뉴 항목 ─────────────────────────────────────────
_HOME_ACTIONS: list[tuple[str, str]] = [
    ("split", "Split   — GIF를 그리드로 분할"),
    ("preview", "Preview — 타일 미리보기"),
    ("upload", "Upload  — Mattermost에 이모지 업로드"),
    ("share", "Share   — 갤러리에 이모지 공유"),
    ("history", "History — 작업 히스토리 조회"),
    ("quit", "Quit"),
]

_DISPATCH = {
    "split": split_cmd,
    "preview": preview_cmd,
    "upload": upload_cmd,
    "share": share_cmd,
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

        history_service = HistoryService()
        latest = history_service.get_latest()
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
