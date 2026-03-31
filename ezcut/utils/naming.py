from __future__ import annotations

import re
import string

NAME_SANITIZE_RE = re.compile(r"[^a-z0-9._-]+")


def piece_id(row: int, col: int, col_pad: int) -> str:
    return f"{string.ascii_lowercase[row]}{col + 1:0{col_pad}d}"


def normalize_emoji_name(stem: str, prefix: str = "") -> str:
    name = f"{prefix}{stem}".lower()
    name = NAME_SANITIZE_RE.sub("-", name).strip("-")
    return name[:64]
