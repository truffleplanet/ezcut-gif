import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from ezcut.services import Previewer
from ezcut.store.models import PreviewConfig
from ezcut.store.state import PreviewTaskState


class PreviewTab:
    """Preview 탭 UI를 구성한다."""

    def __init__(self, parent, task_state: PreviewTaskState) -> None:
        self.task_state = task_state
        self.frame = ttk.Frame(parent, padding=16)
        self.frame.columnconfigure(0, weight=1)

        self.previewer: Previewer | None = None
        self.preview_window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self._after_id: str | None = None
        self._resize_after_id: str | None = None
        self._canvas_items: dict[tuple[int, int], int] = {}
        self._photo_refs: dict[tuple[int, int], ImageTk.PhotoImage] = {}

        self.directory_var = tk.StringVar(
            value=self._path_text(self.task_state.selected_directory)
        )
        self.status_var = tk.StringVar(value=self._status_text())
        self.error_var = tk.StringVar(value=self.task_state.error_message or "-")
        self.popup_status_var = tk.StringVar(value=self._status_text())
        self.popup_error_var = tk.StringVar(value=self.task_state.error_message or "-")

        self._build_form()
        self.directory_var.trace_add("write", self._sync_state)
        self.refresh_task_state()

    def _build_form(self) -> None:
        ttk.Label(self.frame, text="Preview", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            self.frame,
            text="미리보기 대상 디렉토리와 재생 상태를 관리합니다.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        form = ttk.LabelFrame(self.frame, text="입력값", padding=12)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="타일 디렉토리").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        entry_frame = ttk.Frame(form)
        entry_frame.grid(row=0, column=1, sticky="ew", pady=4)
        entry_frame.columnconfigure(0, weight=1)

        ttk.Entry(entry_frame, textvariable=self.directory_var).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(
            entry_frame,
            text="폴더 선택",
            command=self._choose_directory,
        ).grid(row=0, column=1, padx=(8, 0))

        actions = ttk.Frame(self.frame)
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))

        self.load_button = ttk.Button(
            actions, text="불러오기", command=self._load_preview
        )
        self.load_button.pack(side="left")
        ttk.Label(
            self.frame,
            text="미리보기는 별도 창으로 열립니다.",
        ).grid(row=4, column=0, sticky="w", pady=(12, 0))

    def _sync_state(self, *_args) -> None:
        text = self.directory_var.get().strip()
        self.task_state.selected_directory = Path(text) if text else None
        self.refresh_task_state()

    def _choose_directory(self) -> None:
        path = filedialog.askdirectory(
            parent=self.frame,
            title="미리보기 디렉토리 선택",
        )
        if path:
            self.directory_var.set(path)

    def set_directory(self, path: Path) -> None:
        self.directory_var.set(str(path))

    def _load_preview(self) -> None:
        if self.task_state.selected_directory is None:
            self.task_state.error_message = "미리보기 디렉토리를 선택해주세요."
            self.refresh_task_state()
            return

        try:
            self.previewer = Previewer(
                PreviewConfig(directory=self.task_state.selected_directory)
            )
            self.previewer.load()
        except Exception as error:  # noqa: BLE001
            self.task_state.is_loaded = False
            self.task_state.error_message = str(error)
            self.refresh_task_state()
            return

        self._ensure_preview_window()
        self.task_state.is_loaded = True
        self.task_state.is_playing = False
        self.task_state.timeline_ms = 0
        self.task_state.error_message = ""
        self._draw_tiles()
        self.refresh_task_state()

    def _start_preview(self) -> None:
        if not self.task_state.is_loaded:
            self._load_preview()
            if not self.task_state.is_loaded:
                return

        if self._is_preview_finished():
            self._reset_preview()

        self._ensure_preview_window()
        self.task_state.is_playing = True
        self.refresh_task_state()
        self._schedule_next_tick()

    def _stop_preview(self) -> None:
        if self._after_id is not None:
            self.frame.after_cancel(self._after_id)
            self._after_id = None
        self.task_state.is_playing = False
        self.refresh_task_state()

    def _reset_preview(self) -> None:
        self._stop_preview()
        if self.previewer is None:
            return
        self.previewer.reset_all()
        self.task_state.timeline_ms = 0
        self._draw_tiles()
        self.refresh_task_state()

    def _schedule_next_tick(self) -> None:
        if self.previewer is None or not self.task_state.is_playing:
            return

        next_ms = self.previewer.next_event_ms()
        if next_ms is None:
            self.previewer.reset_all()
            self.task_state.timeline_ms = 0
            self._draw_tiles()
            next_ms = self.previewer.next_event_ms()
            if next_ms is None:
                self._stop_preview()
                return

        delay = max(next_ms - self.task_state.timeline_ms, 1)
        self._after_id = self.frame.after(delay, lambda: self._tick(next_ms))

    def _tick(self, event_time_ms: int) -> None:
        if self.previewer is None:
            return

        changed = False
        for tile in self.previewer.tiles:
            if tile.next_change_ms is None:
                continue
            if tile.next_change_ms <= event_time_ms:
                changed |= self.previewer.advance_tile(tile, event_time_ms)

        self.task_state.timeline_ms = event_time_ms
        if changed:
            self._draw_tiles()
        self.refresh_task_state()
        self._schedule_next_tick()

    def _handle_canvas_resize(self, _event) -> None:
        if (
            self.previewer is None
            or not self.task_state.is_loaded
            or self.canvas is None
        ):
            return
        if self._resize_after_id is not None:
            self.frame.after_cancel(self._resize_after_id)
        self._resize_after_id = self.frame.after(40, self._redraw_after_resize)

    def _redraw_after_resize(self) -> None:
        self._resize_after_id = None
        if self.previewer is None or not self.task_state.is_loaded:
            return
        self._draw_tiles()

    def _draw_tiles(self) -> None:
        if self.previewer is None:
            return
        self._ensure_preview_window()
        if self.canvas is None:
            return

        rows, cols, tile_size = self.previewer.grid_info
        width, height = tile_size
        self.canvas.delete("all")
        self._canvas_items.clear()
        self._photo_refs.clear()

        total_width = cols * width
        total_height = rows * height

        available_width = max(self.canvas.winfo_width(), 760)
        available_height = max(self.canvas.winfo_height(), 420)
        scale = min(
            available_width / total_width,
            available_height / total_height,
            1.0,
        )

        draw_width = max(int(width * scale), 1)
        draw_height = max(int(height * scale), 1)
        fitted_width = cols * draw_width
        fitted_height = rows * draw_height
        offset_x = max((available_width - fitted_width) // 2, 0)
        offset_y = max((available_height - fitted_height) // 2, 0)

        self.canvas.configure(scrollregion=(0, 0, available_width, available_height))

        for tile in self.previewer.tiles:
            frame = tile.current_frame
            if scale < 1.0:
                frame = frame.resize(
                    (draw_width, draw_height), Image.Resampling.LANCZOS
                )
            photo = ImageTk.PhotoImage(frame)
            key = (tile.row_index, tile.col_index)
            x = offset_x + tile.col_index * draw_width
            y = offset_y + tile.row_index * draw_height
            item_id = self._canvas_items.get(key)

            if item_id is None:
                self._canvas_items[key] = self.canvas.create_image(
                    x,
                    y,
                    anchor="nw",
                    image=photo,
                )
            else:
                self.canvas.itemconfigure(item_id, image=photo)

            self._photo_refs[key] = photo

    def refresh_task_state(self) -> None:
        """현재 미리보기 상태를 화면 문자열로 갱신한다."""
        self.status_var.set(self._status_text())
        self.error_var.set(self.task_state.error_message or "-")
        self.popup_status_var.set(self._status_text())
        self.popup_error_var.set(self.task_state.error_message or "-")
        if hasattr(self, "popup_start_button"):
            loaded = "normal" if self.task_state.is_loaded else "disabled"
            playing = "normal" if self.task_state.is_playing else "disabled"
            self.popup_start_button.configure(
                state="disabled" if self.task_state.is_playing else loaded
            )
            self.popup_stop_button.configure(state=playing)
            self.popup_reset_button.configure(state=loaded)

    def _status_text(self) -> str:
        if self.task_state.is_playing:
            return f"재생 중 ({self.task_state.timeline_ms}ms)"
        if self.task_state.is_loaded:
            return f"로드 완료 ({self.task_state.timeline_ms}ms)"
        return "대기 중"

    @staticmethod
    def _path_text(value: Path | None) -> str:
        return str(value) if value is not None else ""

    def _ensure_preview_window(self) -> None:
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.deiconify()
            self.preview_window.lift()
            self.preview_window.focus_force()
            return

        top = tk.Toplevel(self.frame)
        top.title("Preview")
        top.geometry("1200x800")
        try:
            top.state("zoomed")
        except tk.TclError:
            pass

        container = ttk.Frame(top, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        actions = ttk.Frame(container)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.popup_start_button = ttk.Button(
            actions, text="시작", command=self._start_preview
        )
        self.popup_start_button.pack(side="left")

        self.popup_stop_button = ttk.Button(
            actions, text="정지", command=self._stop_preview
        )
        self.popup_stop_button.pack(side="left", padx=(8, 0))

        self.popup_reset_button = ttk.Button(
            actions, text="초기화", command=self._reset_preview
        )
        self.popup_reset_button.pack(side="left", padx=(8, 0))

        canvas = tk.Canvas(container, bg="#111111", highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.bind("<Configure>", self._handle_canvas_resize)

        footer = ttk.Frame(container)
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(1, weight=1)

        ttk.Label(footer, text="상태").grid(row=0, column=0, sticky="nw", padx=(0, 8))
        ttk.Label(footer, textvariable=self.popup_status_var).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(footer, text="오류").grid(
            row=1, column=0, sticky="nw", padx=(0, 8), pady=(8, 0)
        )
        ttk.Label(footer, textvariable=self.popup_error_var).grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )

        top.bind("<space>", self._handle_space_key)
        top.bind("<Key-r>", self._handle_reset_key)
        top.bind("<Key-R>", self._handle_reset_key)
        top.protocol("WM_DELETE_WINDOW", self._close_preview_window)

        self.preview_window = top
        self.canvas = canvas
        self.refresh_task_state()

    def _close_preview_window(self) -> None:
        self._stop_preview()
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.withdraw()

    def _handle_space_key(self, _event) -> str:
        if self.task_state.is_playing:
            self._stop_preview()
        else:
            self._start_preview()
        return "break"

    def _handle_reset_key(self, _event) -> str:
        self._reset_preview()
        return "break"

    def _is_preview_finished(self) -> bool:
        if self.previewer is None or not self.previewer.tiles:
            return False
        return all(tile.next_change_ms is None for tile in self.previewer.tiles)
