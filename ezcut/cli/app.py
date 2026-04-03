import typer

from ezcut.cli.commands.history import history_cmd
from ezcut.cli.commands.preview import preview_cmd
from ezcut.cli.commands.share import share_cmd
from ezcut.cli.commands.split import split_cmd
from ezcut.cli.commands.upload import upload_cmd
from ezcut.cli.prompts import ask_select
from ezcut.cli.render import console, render_banner, render_home_status
from ezcut.services.history import HistoryService
from ezcut.services.version import VersionService

app = typer.Typer(
    name="ezcut",
    help="GIF를 그리드로 분할하고 Mattermost 이모지로 업로드합니다.",
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
)

# ── 커맨드 등록 ─────────────────────────────────────
app.command(name="split")(split_cmd)
app.command(name="preview")(preview_cmd)
app.command(name="history")(history_cmd)
app.command(name="upload")(upload_cmd)
app.command(name="share")(share_cmd)


@app.command(name="update")
def update_cmd() -> None:
    """앱 업데이트 방법을 안내합니다."""
    version_service = VersionService()
    current = version_service.get_current_version()
    latest = version_service.get_latest_version(force=True)

    console.print()
    console.rule("[bold cyan]Update Guide[/]")
    console.print()
    console.print(f"  Current version: [bold]{current}[/]")
    if latest:
        console.print(f"  Latest version:  [bold green]{latest}[/]")

    console.print("\n  설치 환경에 맞는 명령어를 실행하여 업데이트하세요:\n")

    console.print("  [bold cyan]1. uv로 설치한 경우 (권장)[/]")
    console.print("     [white]uv tool upgrade ezcut[/]")

    console.print("\n  [bold cyan]2. pipx로 설치한 경우[/]")
    console.print("     [white]pipx upgrade ezcut[/]")

    console.print("\n  [bold cyan]3. pip로 직접 설치한 경우[/]")
    console.print(
        "     [white]pip install --upgrade git+https://github.com/S-P-A-N/ezcut-gif.git[/]"
    )
    console.print()
    console.rule(style="dim")
    console.print()


# ── 홈 메뉴 항목 ─────────────────────────────────────────
_HOME_ACTIONS: list[tuple[str, str]] = [
    ("split", "Split   — GIF를 그리드로 분할"),
    ("preview", "Preview — 타일 미리보기"),
    ("upload", "Upload  — Mattermost에 이모지 업로드"),
    ("share", "Share   — 갤러리에 이모지 공유"),
    ("history", "History — 작업 히스토리 조회"),
    ("update", "Update  — 앱 업데이트 안내"),
    ("quit", "Quit"),
]

_DISPATCH = {
    "split": split_cmd,
    "preview": preview_cmd,
    "upload": upload_cmd,
    "share": share_cmd,
    "history": history_cmd,
    "update": update_cmd,
}


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="버전 정보를 출력하고 종료합니다.",
        is_eager=True,
    ),
) -> None:
    """ezcut 홈 화면."""
    if version:
        version_service = VersionService()
        console.print(f"ezcut v{version_service.get_current_version()}")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    _home_loop(ctx)


def _home_loop(ctx: typer.Context) -> None:
    """홈 화면 루프. 커맨드 완료 후 다시 메뉴로 복귀한다."""
    first_run = True
    version_service = VersionService()
    current_version = version_service.get_current_version()

    while True:
        if first_run:
            latest_version = version_service.get_latest_version()
            render_banner(current_version, latest_version)
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
