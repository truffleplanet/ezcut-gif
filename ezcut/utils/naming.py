import re
import string

NAME_SANITIZE_RE = re.compile(r"[^a-z0-9._-]+")


def piece_id(row: int, col: int, col_pad: int) -> str:
    """타일 식별자 생성. 예: piece_id(0, 0, 2) → 'a01'"""
    return f"{string.ascii_lowercase[row]}{col + 1:0{col_pad}d}"


def normalize_emoji_name(stem: str, prefix: str = "") -> str:
    """이모지 이름 정규화. 소문자 + 특수문자 하이픈 치환, 최대 64자."""
    name = f"{prefix}{stem}".lower()
    name = NAME_SANITIZE_RE.sub("-", name).strip("-")
    return name[:64]
