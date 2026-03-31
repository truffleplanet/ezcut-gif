import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from threading import Thread
from tkinter import filedialog, ttk

from PIL import Image

from ezcut.services import Splitter
from ezcut.store.models import SplitConfig
from ezcut.store.state import SplitFormState, SplitTaskState
from ezcut.utils.grid import compute_grid


class SplitTab:
    """Split 탭 UI를 구성한다."""

    def __init__(
        self,
        parent,
        form_state: SplitFormState,
        task_state: SplitTaskState,
        on_split_complete: Callable[[Path], None] | None = None,
    ) -> None:
        self.form_state = form_state
        self.task_state = task_state
        self.on_split_complete = on_split_complete

        self.frame = ttk.Frame(parent, padding=16)
        self.frame.columnconfigure(0, weight=1)

        self.input_path_var = tk.StringVar(
            value=self._path_text(self.form_state.input_path)
        )
        self.output_dir_var = tk.StringVar(
            value=self._path_text(self.form_state.output_dir)
        )
        self.cols_var = tk.StringVar(value=self._number_text(self.form_state.cols))
        self.rows_var = tk.StringVar(value=self._number_text(self.form_state.rows))
        self.emoji_name_var = tk.StringVar(value=self.form_state.emoji_name)
        self.tile_size_var = tk.StringVar(value=str(self.form_state.tile_size))
        self.max_file_size_var = tk.StringVar(
            value=str(self.form_state.max_file_size_kb)
        )
        self.speed_multiplier_var = tk.StringVar(
            value=self._speed_text(self.form_state.speed_multiplier)
        )
        self.multiplier_var = tk.StringVar(value="1x")

        self.status_var = tk.StringVar(value=self._status_text())
        self.error_var = tk.StringVar(value=self.task_state.error_message or "-")
        self.image_size_var = tk.StringVar(value="-")
        self.recommended_grid_var = tk.StringVar(value="-")
        self.applied_grid_var = tk.StringVar(value=self._current_grid_text())
        self.run_button_state = tk.StringVar(value="normal")

        self._base_cols: int | None = None
        self._base_rows: int | None = None
        self._recommended_cols: int | None = None
        self._recommended_rows: int | None = None
        self._progress_window: tk.Toplevel | None = None
        self._progress_label_var = tk.StringVar(value="")
        self._progress_detail_var = tk.StringVar(value="")

        self._build_form()
        self._bind_state()
        self.refresh_task_state()

    def _build_form(self) -> None:
        ttk.Label(self.frame, text="Split", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            self.frame,
            text="GIF를 여러 조각으로 나누기 위한 설정을 선택합니다.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        form = ttk.LabelFrame(self.frame, text="입력값", padding=12)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self._add_path_row(
            form,
            0,
            "입력 GIF",
            self.input_path_var,
            button_text="파일 선택",
            command=self._choose_input_gif,
        )
        self._add_path_row(
            form,
            1,
            "출력 폴더",
            self.output_dir_var,
            button_text="폴더 선택",
            command=self._choose_output_dir,
        )
        self._add_entry_row(form, 2, "가로 조각 수", self.cols_var, width=10)
        self._add_entry_row(form, 3, "세로 조각 수", self.rows_var, width=10)
        self._add_entry_row(form, 4, "이모지 이름", self.emoji_name_var)
        self._add_entry_row(
            form, 5, "조각 이미지 크기(px)", self.tile_size_var, width=10
        )
        self._add_entry_row(
            form,
            6,
            "조각당 최대 파일 크기(KB)",
            self.max_file_size_var,
            width=10,
        )
        self._add_combobox_row(
            form,
            7,
            "재생 속도",
            self.speed_multiplier_var,
            values=("1.0x", "1.5x"),
            width=10,
        )

        recommendation = ttk.LabelFrame(self.frame, text="자동 추천 분할", padding=12)
        recommendation.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        recommendation.columnconfigure(1, weight=1)

        ttk.Label(recommendation, text="원본 크기").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        ttk.Label(recommendation, textvariable=self.image_size_var).grid(
            row=0,
            column=1,
            sticky="w",
            pady=4,
        )

        ttk.Label(recommendation, text="추천 조각 수").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        ttk.Label(recommendation, textvariable=self.recommended_grid_var).grid(
            row=1,
            column=1,
            sticky="w",
            pady=4,
        )

        ttk.Label(recommendation, text="분할 강도").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        ttk.Combobox(
            recommendation,
            textvariable=self.multiplier_var,
            values=("1x", "2x", "3x", "4x"),
            state="readonly",
            width=8,
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(
            recommendation,
            text="1단계는 기본 추천, 2단계 이상은 더 잘게 나눕니다.",
        ).grid(row=3, column=1, sticky="w")

        ttk.Button(
            recommendation,
            text="추천 조각 수 적용",
            command=self._apply_recommended_grid,
        ).grid(row=4, column=1, sticky="w", pady=(8, 4))

        ttk.Label(recommendation, text="현재 분할 설정").grid(
            row=5,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        ttk.Label(recommendation, textvariable=self.applied_grid_var).grid(
            row=5,
            column=1,
            sticky="w",
            pady=4,
        )

        actions = ttk.Frame(self.frame)
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))

        self.run_button = ttk.Button(
            actions,
            text="분할 시작",
            command=self._start_split,
        )
        self.run_button.pack(anchor="e")

        ttk.Label(
            self.frame,
            text="조각 이미지 크기(px)는 결과 GIF 한 조각의 가로/세로 크기입니다. 예: 128 = 128x128",
        ).grid(row=5, column=0, sticky="w", pady=(12, 0))
        ttk.Label(
            self.frame,
            text="재생 속도는 결과 GIF의 전체 실행 시간을 압축합니다. 예: 1.5x = 약 2/3 시간",
        ).grid(row=6, column=0, sticky="w", pady=(4, 0))

    def _add_entry_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        width: int = 40,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(parent, textvariable=variable, width=width).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4,
        )

    def _add_path_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        button_text: str,
        command,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )

        entry_frame = ttk.Frame(parent)
        entry_frame.grid(row=row, column=1, sticky="ew", pady=4)
        entry_frame.columnconfigure(0, weight=1)

        ttk.Entry(entry_frame, textvariable=variable).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(entry_frame, text=button_text, command=command).grid(
            row=0,
            column=1,
            padx=(8, 0),
        )

    def _add_combobox_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
        width: int = 10,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly",
            width=width,
        ).grid(row=row, column=1, sticky="w", pady=4)

    def _bind_state(self) -> None:
        variables = (
            self.input_path_var,
            self.output_dir_var,
            self.cols_var,
            self.rows_var,
            self.emoji_name_var,
            self.tile_size_var,
            self.max_file_size_var,
            self.speed_multiplier_var,
        )
        for variable in variables:
            variable.trace_add("write", self._sync_form_state)
        self.multiplier_var.trace_add("write", self._sync_recommendation_state)

    def _sync_form_state(self, *_args) -> None:
        self.form_state.input_path = self._parse_path(self.input_path_var.get())
        self.form_state.output_dir = self._parse_path(self.output_dir_var.get())
        self.form_state.cols = self._parse_int(self.cols_var.get())
        self.form_state.rows = self._parse_int(self.rows_var.get())
        self.form_state.emoji_name = self.emoji_name_var.get().strip()
        self.form_state.tile_size = self._parse_int(self.tile_size_var.get()) or 128
        self.form_state.max_file_size_kb = (
            self._parse_int(self.max_file_size_var.get()) or 512
        )
        self.form_state.speed_multiplier = self._parse_speed_multiplier(
            self.speed_multiplier_var.get()
        )
        self.applied_grid_var.set(self._current_grid_text())
        self.refresh_task_state()

    def refresh_task_state(self) -> None:
        """현재 작업 상태를 화면 문자열로 갱신한다."""
        self.status_var.set(self._status_text())
        self.error_var.set(self.task_state.error_message or "-")
        self.run_button.configure(
            state="disabled" if self.task_state.is_running else "normal"
        )

    def _choose_input_gif(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.frame,
            title="입력 GIF 선택",
            filetypes=[("GIF 파일", "*.gif"), ("모든 파일", "*.*")],
        )
        if path:
            self.input_path_var.set(path)
            self._load_gif_metadata(Path(path))
            self._fill_defaults_from_input(Path(path))

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.frame,
            title="출력 폴더 선택",
        )
        if path:
            self.output_dir_var.set(path)

    def _load_gif_metadata(self, path: Path) -> None:
        try:
            with Image.open(path) as image:
                width, height = image.size
        except Exception:  # noqa: BLE001
            self._base_cols = None
            self._base_rows = None
            self._recommended_cols = None
            self._recommended_rows = None
            self.image_size_var.set("-")
            self.recommended_grid_var.set("-")
            return

        self._base_cols, self._base_rows = compute_grid(width, height)
        self._recommended_cols, self._recommended_rows = self._recommend_grid(
            self._base_cols,
            self._base_rows,
        )
        self.image_size_var.set(f"{width} x {height}")
        self.recommended_grid_var.set(
            f"{self._recommended_cols} x {self._recommended_rows}"
        )
        self._apply_recommended_grid()

    def _fill_defaults_from_input(self, path: Path) -> None:
        if not self.emoji_name_var.get().strip():
            self.emoji_name_var.set(path.stem)
        self.output_dir_var.set(str(path.with_name(f"{path.stem}_pieces")))

    def _apply_recommended_grid(self) -> None:
        if self._recommended_cols is None or self._recommended_rows is None:
            return

        multiplier = self._parse_multiplier(self.multiplier_var.get())
        self.cols_var.set(str(self._recommended_cols * multiplier))
        self.rows_var.set(str(self._recommended_rows * multiplier))

    def _sync_recommendation_state(self, *_args) -> None:
        if self._recommended_cols is None or self._recommended_rows is None:
            self.applied_grid_var.set(self._current_grid_text())
            return
        self._apply_recommended_grid()

    def _current_grid_text(self) -> str:
        cols = self.cols_var.get().strip()
        rows = self.rows_var.get().strip()
        if not cols or not rows:
            return "-"
        return f"{cols} x {rows}"

    def _status_text(self) -> str:
        if self.task_state.is_running:
            return (
                f"실행 중 ({self.task_state.current}/{self.task_state.total}) "
                f"{self.task_state.message}".strip()
            )
        if self.task_state.last_result is not None:
            return f"완료: {self.task_state.last_result.output_dir}"
        return "대기 중"

    def _start_split(self) -> None:
        config = self._build_config()
        if config is None:
            return

        self._open_progress_window()
        self.task_state.is_running = True
        self.task_state.current = 0
        self.task_state.total = 0
        self.task_state.message = ""
        self.task_state.error_message = ""
        self.refresh_task_state()

        Thread(target=self._run_split, args=(config,), daemon=True).start()

    def _build_config(self) -> SplitConfig | None:
        if self.form_state.input_path is None:
            self.task_state.error_message = "입력 GIF를 선택해주세요."
            self.refresh_task_state()
            return None

        return SplitConfig(
            input_path=self.form_state.input_path,
            tile_size=self.form_state.tile_size,
            output_dir=self.form_state.output_dir,
            cols=self.form_state.cols,
            rows=self.form_state.rows,
            emoji_name=self.form_state.emoji_name or None,
            max_file_size_kb=self.form_state.max_file_size_kb,
            speed_multiplier=self.form_state.speed_multiplier,
        )

    def _run_split(self, config: SplitConfig) -> None:
        splitter = Splitter(config=config, on_progress=self._handle_progress)
        try:
            result = splitter.run()
        except Exception as error:  # noqa: BLE001
            message = str(error)
            self.frame.after(
                0, lambda message=message: self._finish_split_error(message)
            )
            return

        self.frame.after(
            0, lambda: self._finish_split_success(result.output_dir, result)
        )

    def _handle_progress(self, current: int, total: int, message: str) -> None:
        self.frame.after(
            0,
            lambda: self._update_progress(current, total, message),
        )

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.task_state.current = current
        self.task_state.total = total
        self.task_state.message = message
        self._progress_label_var.set("분할 작업 진행 중")
        self._progress_detail_var.set(f"{current}/{total} {message}".strip())
        self.refresh_task_state()

    def _finish_split_success(self, output_dir: Path, result) -> None:
        self.task_state.is_running = False
        self.task_state.last_result = result
        self.task_state.error_message = ""
        self.task_state.message = "완료"
        self._progress_label_var.set("분할 완료")
        self._progress_detail_var.set(str(output_dir))
        self.refresh_task_state()
        if self.on_split_complete is not None:
            self.on_split_complete(output_dir)

    def _finish_split_error(self, message: str) -> None:
        self.task_state.is_running = False
        self.task_state.error_message = message
        self.task_state.message = ""
        self._progress_label_var.set("분할 실패")
        self._progress_detail_var.set(message)
        self.refresh_task_state()

    def _open_progress_window(self) -> None:
        if self._progress_window is not None and self._progress_window.winfo_exists():
            self._progress_window.deiconify()
            self._progress_window.lift()
            self._progress_window.focus_force()
            return

        top = tk.Toplevel(self.frame)
        top.title("분할 진행 상태")
        top.resizable(False, False)
        top.transient(self.frame.winfo_toplevel())
        top.geometry("420x140")

        container = ttk.Frame(top, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            textvariable=self._progress_label_var,
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            container,
            textvariable=self._progress_detail_var,
            wraplength=360,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Button(
            container,
            text="닫기",
            command=top.withdraw,
        ).pack(anchor="e", pady=(16, 0))

        self._progress_window = top
        self._progress_label_var.set("분할 작업 시작")
        self._progress_detail_var.set("작업 상태를 여기서 확인할 수 있습니다.")

    @staticmethod
    def _parse_int(value: str) -> int | None:
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    @staticmethod
    def _parse_path(value: str) -> Path | None:
        text = value.strip()
        return Path(text) if text else None

    @staticmethod
    def _path_text(value: Path | None) -> str:
        return str(value) if value is not None else ""

    @staticmethod
    def _number_text(value: int | None) -> str:
        return "" if value is None else str(value)

    @staticmethod
    def _parse_multiplier(value: str) -> int:
        text = value.strip().lower().removesuffix("x")
        try:
            return max(int(text), 1)
        except ValueError:
            return 1

    @staticmethod
    def _recommend_grid(
        cols: int,
        rows: int,
        max_pieces: int = 144,
    ) -> tuple[int, int]:
        current_cols = cols
        current_rows = rows

        while current_cols * current_rows > max_pieces:
            next_cols = max(round(current_cols / 2), 1)
            next_rows = max(round(current_rows / 2), 1)
            if next_cols == current_cols and next_rows == current_rows:
                break
            current_cols = next_cols
            current_rows = next_rows

        return current_cols, current_rows

    @staticmethod
    def _parse_speed_multiplier(value: str) -> float:
        text = value.strip().lower().removesuffix("x")
        try:
            return min(max(float(text), 1.0), 1.5)
        except ValueError:
            return 1.0

    @staticmethod
    def _speed_text(value: float) -> str:
        return f"{value:.1f}x"
