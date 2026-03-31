from __future__ import annotations

import re
from pathlib import Path

EMOJI_RE = re.compile(r":([^:]+):")
VALID_IMAGE_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg"}


def parse_emoji_txt(directory: Path) -> list[list[Path]]:
    emoji_path = directory / "emoji.txt"
    if not emoji_path.exists():
        raise FileNotFoundError(f"'{directory}'에 emoji.txt가 없습니다.")

    grid: list[list[Path]] = []
    for line in emoji_path.read_text(encoding="utf-8").splitlines():
        names = EMOJI_RE.findall(line.strip())
        if not names:
            continue
        grid.append([directory / f"{name}.gif" for name in names])

    if not grid:
        raise ValueError("emoji.txt에서 이모지 이름을 찾지 못했습니다.")

    return grid


def write_emoji_txt(
    output_dir: Path,
    emoji_name: str,
    rows: int,
    cols: int,
    piece_id_factory,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    emoji_lines: list[str] = []
    for row in range(rows):
        line = "".join(
            f":{emoji_name}-{piece_id_factory(row, col)}:" for col in range(cols)
        )
        emoji_lines.append(line)

    emoji_path = output_dir / "emoji.txt"
    emoji_path.write_text("\n".join(emoji_lines) + "\n", encoding="utf-8")
    return emoji_path


def list_image_files(directory: Path) -> list[Path]:
    files = [
        path
        for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
    ]
    if not files:
        raise FileNotFoundError("업로드할 gif/png/jpg 파일을 찾지 못했습니다.")
    return files
