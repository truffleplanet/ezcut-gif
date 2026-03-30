import argparse
import re
import sys
import tkinter as tk
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError as exc:
    raise SystemExit(
        "Pillow가 필요합니다. `py -m pip install Pillow` 실행 후 다시 시도하세요."
    ) from exc


EMOJI_RE = re.compile(r":([^:]+):")


@dataclass
class Tile:
    path: Path
    row_index: int
    col_index: int
    image: Image.Image
    frame_index: int
    current_frame: Image.Image
    current_duration_ms: int
    next_change_ms: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="조각난 GIF 타일을 하나의 애니메이션으로 미리보기합니다."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="GIF 타일이 있는 디렉토리 (기본: 현재 디렉토리)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        help="화면 표시 배율. 지정하지 않으면 화면 크기에 맞춰 자동 계산합니다.",
    )
    parser.add_argument(
        "--background",
        default="#000000",
        help="배경색. 기본값: #000000",
    )
    return parser.parse_args()


def parse_emoji_txt(directory: Path) -> list[list[Path]]:
    """emoji.txt에서 파일명 그리드를 파싱한다.

    Returns:
        2D 리스트 [[row0_files], [row1_files], ...]
    """
    emoji_path = directory / "emoji.txt"
    if not emoji_path.exists():
        raise FileNotFoundError(
            f"'{directory}'에 emoji.txt가 없습니다.\n"
            "ezcut으로 먼저 GIF를 분할하세요: py ezcut.py input.gif"
        )

    grid: list[list[Path]] = []
    for line in emoji_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        names = EMOJI_RE.findall(line)
        if not names:
            continue
        grid.append([directory / f"{name}.gif" for name in names])

    if not grid:
        raise ValueError("emoji.txt에서 이모지 이름을 찾지 못했습니다.")

    return grid


def load_first_frame(image: Image.Image) -> tuple[Image.Image, int]:
    frame = image.convert("RGBA").copy()
    duration_ms = max(20, int(image.info.get("duration", 30)))
    return frame, duration_ms


def open_tiles(grid: list[list[Path]]) -> tuple[list[Tile], int, int, tuple[int, int]]:
    rows = len(grid)
    cols = max(len(row) for row in grid)

    sizes: list[tuple[int, int]] = []
    tiles: list[Tile] = []

    for row_idx, row_paths in enumerate(grid):
        for col_idx, path in enumerate(row_paths):
            if not path.exists():
                print(f"Warning: {path} 파일이 없습니다. 건너뜁니다.", file=sys.stderr)
                continue

            image = Image.open(path)
            frame, duration_ms = load_first_frame(image)
            sizes.append(frame.size)

            tiles.append(
                Tile(
                    path=path,
                    row_index=row_idx,
                    col_index=col_idx,
                    image=image,
                    frame_index=0,
                    current_frame=frame,
                    current_duration_ms=duration_ms,
                    next_change_ms=duration_ms,
                )
            )

    if not tiles:
        raise ValueError("유효한 GIF 타일을 불러오지 못했습니다.")

    # 가장 많이 등장하는 크기를 기준으로 통일
    tile_size = Counter(sizes).most_common(1)[0][0]
    for tile in tiles:
        if tile.current_frame.size != tile_size:
            tile.current_frame = tile.current_frame.resize(tile_size, Image.Resampling.LANCZOS)

    return tiles, rows, cols, tile_size


def reset_tile(tile: Tile) -> None:
    tile.image.close()
    tile.image = Image.open(tile.path)
    tile.frame_index = 0
    tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
    tile.next_change_ms = tile.current_duration_ms


def advance_tile(tile: Tile, event_time_ms: int, tile_size: tuple[int, int]) -> bool:
    try:
        tile.image.seek(tile.frame_index + 1)
    except EOFError:
        tile.next_change_ms = None
        return False

    tile.frame_index += 1
    tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
    if tile.current_frame.size != tile_size:
        tile.current_frame = tile.current_frame.resize(tile_size, Image.Resampling.LANCZOS)
    tile.next_change_ms = event_time_ms + tile.current_duration_ms
    return True


class PreviewApp:
    def __init__(
        self,
        tiles: list[Tile],
        rows: int,
        cols: int,
        tile_size: tuple[int, int],
        scale: float | None,
        background: str,
    ) -> None:
        self.tiles = tiles
        self.rows = rows
        self.cols = cols
        self.tile_width, self.tile_height = tile_size
        self.tile_size = tile_size
        self.full_width = cols * self.tile_width
        self.full_height = rows * self.tile_height
        self.scale = scale
        self.timeline_ms = 0
        self.after_id: str | None = None
        self.paused = False

        self.root = tk.Tk()
        self.root.title(
            f"GIF Preview {self.full_width}x{self.full_height} ({self.cols}x{self.rows} tiles)"
        )
        self.root.configure(bg=background)
        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("r", self.restart)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

        self.image_label = tk.Label(self.root, bg=background, bd=0, highlightthickness=0)
        self.image_label.pack(fill="both", expand=True)

        self.canvas_image = Image.new(
            "RGBA",
            (self.full_width, self.full_height),
            Image.new("RGBA", (1, 1), background).getpixel((0, 0)),
        )
        self.draw_all_tiles()
        self.render_frame()
        self.schedule_next_tick()

    def draw_all_tiles(self) -> None:
        for tile in self.tiles:
            self.paste_tile(tile)

    def paste_tile(self, tile: Tile) -> None:
        x = tile.col_index * self.tile_width
        y = tile.row_index * self.tile_height
        self.canvas_image.paste(tile.current_frame, (x, y))

    def computed_scale(self) -> float:
        if self.scale is not None and self.scale > 0:
            return self.scale

        screen_w = max(1, self.root.winfo_screenwidth() - 120)
        screen_h = max(1, self.root.winfo_screenheight() - 160)
        return min(screen_w / self.full_width, screen_h / self.full_height, 1.0)

    def render_frame(self) -> None:
        scale = self.computed_scale()
        if scale != 1.0:
            display = self.canvas_image.resize(
                (max(1, int(self.full_width * scale)), max(1, int(self.full_height * scale))),
                Image.Resampling.NEAREST,
            )
        else:
            display = self.canvas_image

        self.tk_image = ImageTk.PhotoImage(display)
        self.image_label.configure(image=self.tk_image)

    def next_event_ms(self) -> int | None:
        pending = [tile.next_change_ms for tile in self.tiles if tile.next_change_ms is not None]
        return min(pending) if pending else None

    def schedule_next_tick(self) -> None:
        if self.paused:
            return

        next_event = self.next_event_ms()
        if next_event is None:
            self.after_id = self.root.after(300, self.restart)
            return

        delay_ms = max(1, next_event - self.timeline_ms)
        self.after_id = self.root.after(delay_ms, self.tick)

    def tick(self) -> None:
        self.after_id = None
        if self.paused:
            return

        event_time = self.next_event_ms()
        if event_time is None:
            self.restart()
            return

        self.timeline_ms = event_time
        for tile in self.tiles:
            if tile.next_change_ms == event_time and advance_tile(tile, event_time, self.tile_size):
                self.paste_tile(tile)

        self.render_frame()
        self.schedule_next_tick()

    def toggle_pause(self, _event=None) -> None:
        self.paused = not self.paused
        if self.paused and self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        elif not self.paused and self.after_id is None:
            self.schedule_next_tick()

    def restart(self, _event=None) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.timeline_ms = 0
        for tile in self.tiles:
            reset_tile(tile)

        self.draw_all_tiles()
        self.render_frame()
        if not self.paused:
            self.schedule_next_tick()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    args = parse_args()
    directory = Path(args.directory)

    if not directory.is_dir():
        sys.exit(f"Error: '{directory}'는 유효한 디렉토리가 아닙니다.")

    grid = parse_emoji_txt(directory)
    tiles, rows, cols, tile_size = open_tiles(grid)

    app = PreviewApp(
        tiles=tiles,
        rows=rows,
        cols=cols,
        tile_size=tile_size,
        scale=args.scale,
        background=args.background,
    )
    print(
        f"Loaded {len(tiles)} tiles | layout: {rows} rows x {cols} cols | "
        f"frame size: {tile_size[0]}x{tile_size[1]} | canvas: {cols * tile_size[0]}x{rows * tile_size[1]}"
    )
    print("Controls: space = pause/resume, r = restart, esc = close")
    app.run()


if __name__ == "__main__":
    main()
