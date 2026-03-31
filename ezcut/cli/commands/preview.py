"""ezcut preview 커맨드.

Tk 기반 경량 미리보기 창을 열어 타일 GIF 애니메이션을 재생한다.
Space=일시정지/재생, R=초기화, Escape/Q=종료.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from time import monotonic
from typing import Annotated, Optional

import typer
from PIL import Image, ImageTk

from ...services.previewer import Previewer
from ...store.models import PreviewConfig
from ..render import print_dim, print_error


def preview_cmd(
    directory: Annotated[
        Optional[Path],
        typer.Argument(
            help="미리보기할 타일 디렉토리",
            show_default=False,
        ),
    ] = None,
    last: Annotated[
        bool,
        typer.Option("--last", help="가장 최근 split 결과를 미리보기"),
    ] = False,
) -> None:
    """타일 GIF를 Tk 창에서 미리보기한다."""
    if last:
        directory = _resolve_last()

    if directory is None:
        from ..prompts import ask_directory, step_header

        step_header(1, 1, "미리보기 대상")
        directory = ask_directory("타일 디렉토리", must_exist=True)

    config = PreviewConfig(directory=directory)
    previewer = Previewer(config)

    try:
        previewer.load()
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc

    rows, cols, tile_size = previewer.grid_info
    print_dim(f"{cols}x{rows} grid, tile {tile_size[0]}x{tile_size[1]}px")
    print_dim("Space=재생/정지  R=초기화  Esc/Q=종료")

    _open_preview_window(previewer)


def _resolve_last() -> Path:
    """최근 히스토리에서 출력 디렉토리를 가져온다."""
    from ...repository.history import HistoryRepository

    latest = HistoryRepository().latest()
    if latest is None:
        print_error("히스토리가 비어 있습니다. 먼저 split을 실행해주세요.")
        raise typer.Exit(1)
    path = Path(latest.output_dir)
    if not path.is_dir():
        print_error(f"디렉토리를 찾을 수 없습니다: {path}")
        raise typer.Exit(1)
    print_dim(f"Using latest: {latest.emoji_name} ({path})")
    return path


# ── Tk 미리보기 창 ────────────────────────────────────────


def _open_preview_window(previewer: Previewer) -> None:
    """경량 Tk 미리보기 창을 열고 애니메이션을 재생한다."""
    root = tk.Tk()
    root.title("ezcut preview")
    root.configure(bg="#111111")

    rows, cols, tile_size = previewer.grid_info
    tw, th = tile_size
    native_w, native_h = cols * tw, rows * th

    # 화면 크기 기반 초기 윈도우 사이즈
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    init_w = min(native_w + 40, int(screen_w * 0.85))
    init_h = min(native_h + 80, int(screen_h * 0.85))
    root.geometry(f"{init_w}x{init_h}")

    # 상태 바
    status_var = tk.StringVar(value="Playing")
    status_bar = tk.Label(
        root,
        textvariable=status_var,
        bg="#1a1a1a",
        fg="#00bcd4",
        font=("Consolas", 10),
        anchor="w",
        padx=12,
        pady=4,
    )
    status_bar.pack(side="bottom", fill="x")

    # 캔버스
    canvas = tk.Canvas(root, bg="#111111", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # 상태 관리
    state = _PreviewState(previewer, canvas, status_var, native_w, native_h)
    state.build_composite()
    state.render()
    state.start()

    # 키 바인딩
    def _on_space(_e: tk.Event) -> str:
        if state.playing:
            state.stop()
        else:
            state.start()
        return "break"

    def _on_reset(_e: tk.Event) -> str:
        state.reset()
        state.start()
        return "break"

    def _on_quit(_e: tk.Event) -> None:
        state.stop()
        root.destroy()

    def _on_resize(_e: tk.Event) -> None:
        state.render()

    root.bind("<space>", _on_space)
    root.bind("<Key-r>", _on_reset)
    root.bind("<Key-R>", _on_reset)
    root.bind("<Escape>", _on_quit)
    root.bind("<Key-q>", _on_quit)
    root.bind("<Key-Q>", _on_quit)
    canvas.bind("<Configure>", _on_resize)

    root.mainloop()


class _PreviewState:
    """미리보기 창의 애니메이션 상태를 관리한다."""

    def __init__(
        self,
        previewer: Previewer,
        canvas: tk.Canvas,
        status_var: tk.StringVar,
        native_w: int,
        native_h: int,
    ) -> None:
        self.previewer = previewer
        self.canvas = canvas
        self.status_var = status_var
        self.native_w = native_w
        self.native_h = native_h
        self.playing = False
        self.timeline_ms = 0
        self._after_id: str | None = None
        self._started_at: float | None = None
        self._started_timeline_ms = 0
        self._composite: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None

    def build_composite(self) -> None:
        """전체 타일을 하나의 이미지로 합성한다."""
        tw, th = self.previewer.tile_size
        img = Image.new("RGBA", (self.native_w, self.native_h), "#111111")
        for tile in self.previewer.tiles:
            x = tile.col_index * tw
            y = tile.row_index * th
            img.paste(tile.current_frame, (x, y))
        self._composite = img

    def _paste_tile(self, tile) -> None:
        if self._composite is None:
            return
        tw, th = self.previewer.tile_size
        x = tile.col_index * tw
        y = tile.row_index * th
        self._composite.paste(tile.current_frame, (x, y))

    def render(self) -> None:
        """현재 composite를 캔버스에 맞춰 표시한다."""
        if self._composite is None:
            return
        cw = max(self.canvas.winfo_width(), 100)
        ch = max(self.canvas.winfo_height(), 100)
        scale = min(cw / self.native_w, ch / self.native_h, 1.0)

        if scale < 1.0:
            fw = max(int(self.native_w * scale), 1)
            fh = max(int(self.native_h * scale), 1)
            display = self._composite.resize((fw, fh), Image.Resampling.NEAREST)
        else:
            display = self._composite
            fw, fh = self.native_w, self.native_h

        ox = max((cw - fw) // 2, 0)
        oy = max((ch - fh) // 2, 0)

        self.canvas.delete("all")
        self._photo = ImageTk.PhotoImage(display)
        self.canvas.create_image(ox, oy, anchor="nw", image=self._photo)

    def start(self) -> None:
        if self._all_finished():
            self.reset()
        self.playing = True
        self._started_at = monotonic()
        self._started_timeline_ms = self.timeline_ms
        self._update_status()
        self._schedule()

    def stop(self) -> None:
        if self._after_id is not None:
            self.canvas.after_cancel(self._after_id)
            self._after_id = None
        self.playing = False
        self._started_at = None
        self._update_status()

    def reset(self) -> None:
        self.stop()
        self.previewer.reset_all()
        self.timeline_ms = 0
        self.build_composite()
        self.render()

    def _schedule(self) -> None:
        if not self.playing:
            return
        next_ms = self.previewer.next_event_ms()
        if next_ms is None:
            # 루프 재생
            self.previewer.reset_all()
            self.timeline_ms = 0
            self._started_at = monotonic()
            self._started_timeline_ms = 0
            self.build_composite()
            self.render()
            next_ms = self.previewer.next_event_ms()
            if next_ms is None:
                self.stop()
                return

        if self._started_at is None:
            self._started_at = monotonic()
            self._started_timeline_ms = self.timeline_ms

        target = self._started_at + (next_ms - self._started_timeline_ms) / 1000
        delay = max(int((target - monotonic()) * 1000), 1)
        self._after_id = self.canvas.after(delay, lambda: self._tick(next_ms))

    def _tick(self, event_time_ms: int) -> None:
        changed = False
        for tile in self.previewer.tiles:
            if tile.next_change_ms is not None and tile.next_change_ms <= event_time_ms:
                if self.previewer.advance_tile(tile, event_time_ms):
                    self._paste_tile(tile)
                    changed = True
        self.timeline_ms = event_time_ms
        if changed:
            self.render()
        self._schedule()

    def _all_finished(self) -> bool:
        return all(t.next_change_ms is None for t in self.previewer.tiles)

    def _update_status(self) -> None:
        if self.playing:
            self.status_var.set("Playing  |  Space=정지  R=초기화  Esc=종료")
        else:
            self.status_var.set("Paused   |  Space=재생  R=초기화  Esc=종료")
