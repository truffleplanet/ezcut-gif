import re
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from threading import Thread
from tkinter import filedialog, ttk

from ezcut.repository import ConfigRepository, CredentialRepository
from ezcut.services import Uploader
from ezcut.store.models import UploadConfig
from ezcut.store.state import UploadFormState, UploadTaskState
from ezcut.utils.emoji_txt import list_image_files


class UploadTab:
    """Upload 탭 UI를 구성한다."""

    FAILED_INDEX_RE = re.compile(r"-([a-z]\d+)$", re.IGNORECASE)

    def __init__(
        self,
        parent,
        form_state: UploadFormState,
        task_state: UploadTaskState,
    ) -> None:
        self.form_state = form_state
        self.task_state = task_state
        self.config_repo = ConfigRepository()
        self.credentials_repo = CredentialRepository()
        self.app_config = self.config_repo.load()

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
        self.email_var = tk.StringVar(value=self.app_config.mattermost_email)
        self.password_var = tk.StringVar()

        self.status_var = tk.StringVar(value=self._status_text())
        self.error_var = tk.StringVar(value=self.task_state.error_message or "-")
        self.failed_indices_var = tk.StringVar(value="-")
        self.account_status_var = tk.StringVar(value=self._account_status_text())

        self._build_form()
        self._bind_state()
        self.refresh_task_state()

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

        account = ttk.LabelFrame(self.frame, text="Mattermost 계정", padding=12)
        account.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        account.columnconfigure(1, weight=1)

        self._add_entry_row(account, 0, "이메일", self.email_var)
        self._add_entry_row(
            account,
            1,
            "비밀번호",
            self.password_var,
            show="*",
        )

        account_actions = ttk.Frame(account)
        account_actions.grid(row=2, column=1, sticky="w", pady=(8, 0))

        ttk.Button(
            account_actions,
            text="계정 저장",
            command=self._save_credentials,
        ).pack(side="left")

        ttk.Label(
            account,
            textvariable=self.account_status_var,
        ).grid(row=3, column=1, sticky="w", pady=(8, 0))

        actions = ttk.Frame(self.frame)
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))

        self.run_button = ttk.Button(
            actions,
            text="업로드 시작",
            command=self._start_upload,
        )
        self.run_button.pack(anchor="e")

        status = ttk.LabelFrame(self.frame, text="작업 상태", padding=12)
        status.grid(row=5, column=0, sticky="ew", pady=(12, 0))
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
        ttk.Label(status, text="실패 인덱스").grid(
            row=2, column=0, sticky="nw", padx=(0, 8), pady=(8, 0)
        )
        ttk.Label(
            status,
            textvariable=self.failed_indices_var,
            wraplength=520,
            justify="left",
        ).grid(row=2, column=1, sticky="w", pady=(8, 0))

    def _add_entry_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        width: int = 40,
        show: str | None = None,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(
            parent,
            textvariable=variable,
            width=width,
            show=show or "",
        ).grid(
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

    def _save_credentials(self) -> None:
        email = self.email_var.get().strip()
        password = self.password_var.get()

        if not email:
            self.account_status_var.set("이메일을 입력해주세요.")
            return

        if not password:
            self.account_status_var.set("비밀번호를 입력해주세요.")
            return

        updated_config = replace(self.config_repo.load(), mattermost_email=email)
        self.config_repo.save(updated_config)
        self.app_config = updated_config
        self.credentials_repo.set_password(email, password)
        self.password_var.set("")
        self.account_status_var.set("계정이 저장되었습니다.")

    def refresh_task_state(self) -> None:
        """현재 업로드 상태를 화면 문자열로 갱신한다."""
        self.status_var.set(self._status_text())
        self.error_var.set(self.task_state.error_message or "-")
        self.failed_indices_var.set(self._failed_indices_text())
        self.account_status_var.set(self._account_status_text())
        self.run_button.configure(
            state="disabled" if self.task_state.is_running else "normal"
        )

    def _status_text(self) -> str:
        if self.task_state.is_running:
            return (
                f"실행 중 ({self.task_state.current}/{self.task_state.total}) "
                f"성공 {self.task_state.success}"
            )
        if self.task_state.success or self.task_state.failed:
            return f"완료: 성공 {self.task_state.success}, 실패 {len(self.task_state.failed)}"
        return "대기 중"

    def _start_upload(self) -> None:
        config = self._build_config()
        if config is None:
            return

        self.task_state.is_running = True
        self.task_state.current = 0
        self.task_state.total = 0
        self.task_state.message = ""
        self.task_state.success = 0
        self.task_state.failed.clear()
        self.task_state.error_message = (
            "브라우저가 열리면 터미널에서 Enter를 눌러 업로드를 계속 진행하세요."
        )
        self.refresh_task_state()

        Thread(target=self._run_upload, args=(config,), daemon=True).start()

    def _build_config(self) -> UploadConfig | None:
        if self.form_state.directory is None:
            self.task_state.error_message = "업로드 디렉토리를 선택해주세요."
            self.refresh_task_state()
            return None

        return UploadConfig(
            directory=self.form_state.directory,
            base_url=self.form_state.base_url,
            add_path=self.form_state.add_path,
            pause=self.form_state.pause,
            headless=self.form_state.headless,
            start_index=self.form_state.start_index,
            limit=self.form_state.limit,
            name_prefix=self.form_state.name_prefix,
            login_mode=self.form_state.login_mode,
        )

    def _run_upload(self, config: UploadConfig) -> None:
        uploader = Uploader(config=config, on_progress=self._handle_progress)
        try:
            result = uploader.run()
        except Exception as error:  # noqa: BLE001
            message = str(error)
            self.frame.after(
                0,
                lambda message=message: self._finish_upload_error(message),
            )
            return

        self.frame.after(0, lambda: self._finish_upload_success(result))

    def _handle_progress(self, current: int, total: int, message: str) -> None:
        self.frame.after(
            0,
            lambda: self._update_progress(current, total, message),
        )

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.task_state.current = current
        self.task_state.total = total
        self.task_state.message = message
        self.refresh_task_state()

    def _finish_upload_success(self, result) -> None:
        self.task_state.is_running = False
        self.task_state.success = result.success
        self.task_state.failed = list(result.failed)
        self.task_state.message = ""
        self.task_state.error_message = ""
        self.refresh_task_state()

    def _finish_upload_error(self, message: str) -> None:
        self.task_state.is_running = False
        self.task_state.message = ""
        self.task_state.error_message = message
        self.refresh_task_state()

    def _account_status_text(self) -> str:
        email = self.email_var.get().strip() or self.app_config.mattermost_email
        if not email:
            return "저장된 계정이 없습니다."

        if self.credentials_repo.has_password(email):
            return f"저장된 계정: {email}"

        return f"이메일만 저장됨: {email}"

    def _failed_indices_text(self) -> str:
        if not self.task_state.failed:
            return "-"

        order_map = self._upload_order_map()
        indices: list[str] = []
        for path, _reason in self.task_state.failed:
            match = self.FAILED_INDEX_RE.search(path.stem)
            order = order_map.get(path)
            if match:
                token = match.group(1).lower()
            else:
                token = path.stem

            if order is not None:
                indices.append(f"{token} ({order}번)")
            else:
                indices.append(token)

        return ", ".join(indices)

    def _upload_order_map(self) -> dict[Path, int]:
        directory = self.form_state.directory
        if directory is None or not directory.exists():
            return {}

        try:
            files = list_image_files(directory)
        except Exception:  # noqa: BLE001
            return {}

        start = max(self.form_state.start_index - 1, 0)
        files = files[start:]
        if self.form_state.limit is not None:
            files = files[: self.form_state.limit]

        return {path: start + offset for offset, path in enumerate(files, start=1)}

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
