import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from ezcut.store.state import UploadFormState, UploadTaskState


class UploadTab:
    """Upload 탭 UI를 구성한다."""

    def __init__(
        self,
        parent,
        form_state: UploadFormState,
        task_state: UploadTaskState,
    ) -> None:
        self.form_state = form_state
        self.task_state = task_state

        self.frame = ttk.Frame(parent, padding=16)
        self.frame.columnconfigure(0, weight=1)

        self.directory_var = tk.StringVar(
            value=self._path_text(self.form_state.directory)
        )
        self.base_url_var = tk.StringVar(value=self.form_state.base_url)
        self.add_path_var = tk.StringVar(value=self.form_state.add_path)
        self.pause_var = tk.StringVar(value=str(self.form_state.pause))
        self.headless_var = tk.BooleanVar(value=self.form_state.headless)
        self.start_index_var = tk.StringVar(value=str(self.form_state.start_index))
        self.limit_var = tk.StringVar(value=self._number_text(self.form_state.limit))
        self.name_prefix_var = tk.StringVar(value=self.form_state.name_prefix)
        self.login_mode_var = tk.StringVar(value=self.form_state.login_mode)

        self.status_var = tk.StringVar(value=self._status_text())
        self.error_var = tk.StringVar(value=self.task_state.error_message or "-")

        self._build_form()
        self._bind_state()

    def _build_form(self) -> None:
        ttk.Label(self.frame, text="Upload", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            self.frame,
            text="업로드 입력값과 진행 상태를 관리합니다.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        form = ttk.LabelFrame(self.frame, text="입력값", padding=12)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self._add_path_row(
            form,
            0,
            "타일 디렉토리",
            self.directory_var,
            button_text="폴더 선택",
            command=self._choose_directory,
        )
        self._add_entry_row(form, 1, "Base URL", self.base_url_var)
        self._add_entry_row(form, 2, "추가 경로", self.add_path_var)
        self._add_entry_row(form, 3, "Pause", self.pause_var, width=12)
        self._add_entry_row(form, 4, "Start Index", self.start_index_var, width=12)
        self._add_entry_row(form, 5, "Limit", self.limit_var, width=12)
        self._add_entry_row(form, 6, "이름 Prefix", self.name_prefix_var)

        ttk.Label(form, text="Login Mode").grid(
            row=7,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=4,
        )
        ttk.Combobox(
            form,
            textvariable=self.login_mode_var,
            values=("manual", "auto"),
            state="readonly",
        ).grid(row=7, column=1, sticky="w", pady=4)

        ttk.Checkbutton(
            form,
            text="Headless",
            variable=self.headless_var,
        ).grid(row=8, column=1, sticky="w", pady=(4, 0))

        status = ttk.LabelFrame(self.frame, text="작업 상태", padding=12)
        status.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        status.columnconfigure(1, weight=1)

        ttk.Label(status, text="상태").grid(row=0, column=0, sticky="nw", padx=(0, 8))
        ttk.Label(status, textvariable=self.status_var).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(status, text="오류").grid(
            row=1, column=0, sticky="nw", padx=(0, 8), pady=(8, 0)
        )
        ttk.Label(status, textvariable=self.error_var).grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )

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

    def _bind_state(self) -> None:
        variables = (
            self.directory_var,
            self.base_url_var,
            self.add_path_var,
            self.pause_var,
            self.start_index_var,
            self.limit_var,
            self.name_prefix_var,
            self.login_mode_var,
        )
        for variable in variables:
            variable.trace_add("write", self._sync_form_state)
        self.headless_var.trace_add("write", self._sync_form_state)

    def _sync_form_state(self, *_args) -> None:
        self.form_state.directory = self._parse_path(self.directory_var.get())
        self.form_state.base_url = self.base_url_var.get().strip()
        self.form_state.add_path = self.add_path_var.get().strip()
        self.form_state.pause = self._parse_float(self.pause_var.get()) or 0.3
        self.form_state.headless = self.headless_var.get()
        self.form_state.start_index = self._parse_int(self.start_index_var.get()) or 1
        self.form_state.limit = self._parse_int(self.limit_var.get())
        self.form_state.name_prefix = self.name_prefix_var.get().strip()
        self.form_state.login_mode = self.login_mode_var.get().strip() or "manual"
        self.refresh_task_state()

    def _choose_directory(self) -> None:
        path = filedialog.askdirectory(
            parent=self.frame,
            title="업로드 디렉토리 선택",
        )
        if path:
            self.directory_var.set(path)

    def set_directory(self, path: Path) -> None:
        self.directory_var.set(str(path))

    def refresh_task_state(self) -> None:
        """현재 업로드 상태를 화면 문자열로 갱신한다."""
        self.status_var.set(self._status_text())
        self.error_var.set(self.task_state.error_message or "-")

    def _status_text(self) -> str:
        if self.task_state.is_running:
            return (
                f"실행 중 ({self.task_state.current}/{self.task_state.total}) "
                f"성공 {self.task_state.success}"
            )
        if self.task_state.success or self.task_state.failed:
            return f"완료: 성공 {self.task_state.success}, 실패 {len(self.task_state.failed)}"
        return "대기 중"

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
    def _parse_float(value: str) -> float | None:
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
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
