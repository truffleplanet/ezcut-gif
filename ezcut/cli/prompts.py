"""재사용 가능한 인터랙티브 프롬프트 시스템.

questionary 기반 arrow-key 선택, 경로 자동완성, 미쿠 테마 스타일을 제공한다.
새로운 커맨드를 추가할 때 이 모듈의 함수를 조합하여 위자드를 구성한다.
"""

from __future__ import annotations

from pathlib import Path

import questionary
from questionary import Style

from .render import console

# ── 미쿠 테마 스타일 ──────────────────────────────────────
_STYLE = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "fg:white bold"),
        ("answer", "fg:cyan bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:cyan"),
        ("separator", "fg:#6c6c6c"),
        ("instruction", "fg:#6c6c6c"),
        ("text", "fg:white"),
    ]
)

_QMARK = "\u276f"  # ❯


# ── 스텝 헤더 ─────────────────────────────────────────────


def step_header(current: int, total: int, title: str) -> None:
    """위자드 스텝 헤더를 출력한다.  예: [1/4] GIF 파일 경로"""
    console.print(f"\n  [cyan][{current}/{total}][/] [bold cyan]{title}[/]")


# ── 기본 프롬프트 ─────────────────────────────────────────


def ask_text(
    label: str,
    *,
    default: str = "",
    hint: str = "",
) -> str:
    """텍스트 입력을 받는다."""
    instruction = f"({hint})" if hint else None
    result = questionary.text(
        label,
        default=default,
        instruction=instruction,
        qmark=_QMARK,
        style=_STYLE,
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def ask_int(
    label: str,
    *,
    default: int | None = None,
    hint: str = "",
) -> int | None:
    """정수 입력을 받는다. 빈 입력 시 None을 반환한다."""
    instruction = f"({hint})" if hint else None
    raw = questionary.text(
        label,
        default=str(default) if default is not None else "",
        instruction=instruction,
        qmark=_QMARK,
        style=_STYLE,
        validate=lambda val: (
            True
            if not val.strip()
            else (True if val.strip().lstrip("-").isdigit() else "정수를 입력해주세요")
        ),
    ).ask()
    if raw is None:
        raise KeyboardInterrupt
    raw = raw.strip()
    if not raw:
        return default if default is not None else None
    return int(raw)


def ask_float(
    label: str,
    *,
    default: float | None = None,
    hint: str = "",
) -> float | None:
    """실수 입력을 받는다."""
    instruction = f"({hint})" if hint else None

    def _validate(val: str) -> bool | str:
        if not val.strip():
            return True
        try:
            float(val)
        except ValueError:
            return "숫자를 입력해주세요"
        return True

    raw = questionary.text(
        label,
        default=str(default) if default is not None else "",
        instruction=instruction,
        qmark=_QMARK,
        style=_STYLE,
        validate=_validate,
    ).ask()
    if raw is None:
        raise KeyboardInterrupt
    raw = raw.strip()
    if not raw:
        return default if default is not None else None
    return float(raw)


def ask_confirm(label: str, *, default: bool = True) -> bool:
    """Y/n 확인을 받는다."""
    result = questionary.confirm(
        label,
        default=default,
        qmark=_QMARK,
        style=_STYLE,
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


def ask_select(
    label: str,
    choices: list[tuple[str, str]],
    *,
    default: str | None = None,
) -> str:
    """Arrow-key 선택 프롬프트. choices는 [(key, description), ...] 형태.

    반환값은 선택된 항목의 key.
    """
    q_choices = [questionary.Choice(title=desc, value=key) for key, desc in choices]
    default_choice = default or (choices[0][0] if choices else None)

    result = questionary.select(
        label,
        choices=q_choices,
        default=default_choice,
        qmark=_QMARK,
        style=_STYLE,
        instruction="(↑↓ 선택, Enter 확인)",
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return result


# ── 경로 프롬프트 ─────────────────────────────────────────


def ask_file_path(
    label: str,
    *,
    must_exist: bool = True,
    suffix: str = "",
) -> Path:
    """파일 경로를 입력받고 검증한다. Tab 자동완성 지원."""

    def _validate(val: str) -> bool | str:
        if not val.strip():
            return "경로를 입력해주세요"
        path = Path(val).expanduser()
        if must_exist and not path.is_file():
            return f"파일을 찾을 수 없습니다: {path}"
        if suffix and not path.name.lower().endswith(suffix.lower()):
            return f"{suffix} 파일이 아닙니다: {path.name}"
        return True

    result = questionary.path(
        label,
        qmark=_QMARK,
        style=_STYLE,
        validate=_validate,
        only_directories=False,
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return Path(result).expanduser().resolve()


def ask_directory(
    label: str,
    *,
    must_exist: bool = False,
    default: str = "",
) -> Path:
    """디렉토리 경로를 입력받는다. Tab 자동완성 지원."""

    def _validate(val: str) -> bool | str:
        if not val.strip():
            return "경로를 입력해주세요"
        if must_exist and not Path(val).expanduser().is_dir():
            return f"디렉토리를 찾을 수 없습니다: {val}"
        return True

    result = questionary.path(
        label,
        default=default,
        qmark=_QMARK,
        style=_STYLE,
        validate=_validate,
        only_directories=True,
    ).ask()
    if result is None:
        raise KeyboardInterrupt
    return Path(result).expanduser().resolve()


# ── 복합 프롬프트 (커맨드에서 직접 사용) ──────────────────


def prompt_input_path() -> Path:
    """GIF 파일 경로를 대화형으로 입력받는다."""
    return ask_file_path("GIF 파일 경로", suffix=".gif")


def prompt_output_dir(default_name: str = "") -> Path:
    """출력 디렉토리를 대화형으로 입력받는다."""
    default = f"./{default_name}_pieces" if default_name else ""
    return ask_directory("출력 디렉토리", default=default)


def prompt_emoji_name(default: str = "") -> str:
    """이모지 이름을 대화형으로 입력받는다."""
    return ask_text("이모지 이름", default=default, hint="Enter=파일명 사용")
