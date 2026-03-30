import argparse
import re
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError as exc:
    raise SystemExit(
        "Pillow가 필요합니다. `py -m pip install Pillow` 실행 후 다시 시도하세요."
    ) from exc


FILE_RE = re.compile(r"^(?P<prefix>.*?)(?P<row>[a-zA-Z])(?P<col>\d+)\.gif$")


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
        "--glob",
        default="ai-*.gif",
        help="타일 파일 패턴. 기본값: ai-*.gif",
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


def discover_layout(paths: list[Path]) -> tuple[dict[str, int], dict[str, int]]:
    row_labels: set[str] = set()
    col_labels: set[str] = set()

    for path in paths:
        match = FILE_RE.match(path.name)
        if not match:
            continue
        row_labels.add(match.group("row").lower())
        col_labels.add(match.group("col"))

    if not row_labels or not col_labels:
        raise ValueError("행/열 규칙을 파일명에서 찾지 못했습니다.")

    row_map = {label: index for index, label in enumerate(sorted(row_labels))}
    ordered_cols = sorted(col_labels, key=lambda value: int(value))
    col_map = {label: index for index, label in enumerate(ordered_cols)}
    return row_map, col_map


def load_first_frame(image: Image.Image) -> tuple[Image.Image, int]:
    frame = image.convert("RGBA").copy()
    duration_ms = max(20, int(image.info.get("duration", 30)))
    return frame, duration_ms


def open_tiles(glob_pattern: str) -> tuple[list[Tile], int, int, tuple[int, int]]:
    paths = sorted(Path(".").glob(glob_pattern))
    if not paths:
        raise FileNotFoundError(f"`{glob_pattern}` 패턴에 맞는 GIF를 찾지 못했습니다.")

    row_map, col_map = discover_layout(paths)
    tiles: list[Tile] = []
    tile_size: tuple[int, int] | None = None

    for path in paths:
        match = FILE_RE.match(path.name)
        if not match:
            continue

        image = Image.open(path)
        frame, duration_ms = load_first_frame(image)

        if tile_size is None:
            tile_size = frame.size
        elif frame.size != tile_size:
            raise ValueError(
                f"타일 크기가 다릅니다: {path.name} = {frame.size}, expected = {tile_size}"
            )

        tiles.append(
            Tile(
                path=path,
                row_index=row_map[match.group("row").lower()],
                col_index=col_map[match.group("col")],
                image=image,
                frame_index=0,
                current_frame=frame,
                current_duration_ms=duration_ms,
                next_change_ms=duration_ms,
            )
        )

    if tile_size is None:
        raise ValueError("유효한 GIF 타일을 불러오지 못했습니다.")

    return tiles, len(row_map), len(col_map), tile_size


def reset_tile(tile: Tile) -> None:
    tile.image.close()
    tile.image = Image.open(tile.path)
    tile.frame_index = 0
    tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
    tile.next_change_ms = tile.current_duration_ms


def advance_tile(tile: Tile, event_time_ms: int) -> bool:
    try:
        tile.image.seek(tile.frame_index + 1)
    except EOFError:
        tile.next_change_ms = None
        return False

    tile.frame_index += 1
    tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
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
            if tile.next_change_ms == event_time and advance_tile(tile, event_time):
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
    tiles, rows, cols, tile_size = open_tiles(args.glob)
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
