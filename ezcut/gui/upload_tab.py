import re
import tkinter as tk
from pathlib import Path
from threading import Event, Thread
from tkinter import filedialog, messagebox, ttk

from ezcut.services.auth import AuthService
from ezcut.services.config import ConfigService
from ezcut.services.gallery import GalleryAPIError, GalleryService
from ezcut.services.history import HistoryNotFoundError, HistoryService
from ezcut.services.uploader import Uploader
from ezcut.store.models import GalleryConfig, UploadConfig
from ezcut.store.state import UploadFormState, UploadTaskState


class UploadTab:
    """Upload 탭 UI를 구성한다."""

    FAILED_INDEX_RE = re.compile(r"-([a-z]\d+)$", re.IGNORECASE)

    def __init__(
        self,
        parent: tk.Widget,
        form_state: UploadFormState,
        task_state: UploadTaskState,
    ) -> None:
        self.form_state = form_state
        self.task_state = task_state
        self.config_service = ConfigService()
        self.auth_service = AuthService()
        self.app_config = self.config_service.load_config()

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
        self._manual_login_window: tk.Toplevel | None = None
        self._manual_login_event: Event | None = None
        self.share_button: ttk.Button | None = None
        self._upload_succeeded = False  # 이번 세션에서 업로드 성공 여부

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

        self.share_button = ttk.Button(
            actions,
            text="갤러리에 공유",
            command=self._start_gallery_share,
        )
        self.share_button.pack(side="right", padx=(0, 8))

        self.run_button = ttk.Button(
            actions,
            text="업로드 시작",
            command=self._start_upload,
        )
        self.run_button.pack(side="right")

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
        previous_directory = self.form_state.directory
        self.form_state.directory = self._parse_path(self.directory_var.get())
        if self.form_state.directory != previous_directory:
            self._upload_succeeded = False
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
            return

        self.config_service.update_mattermost_email(email)
        self.app_config = self.config_service.load_config()
        self.auth_service.set_password(email, password)
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
        if self.share_button is not None:
            share_enabled = not self.task_state.is_running and (
                self._upload_succeeded or self._has_shareable_history_entry()
            )
            self.share_button.configure(state="normal" if share_enabled else "disabled")

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
        self.app_config = self.config_service.load_config()
        config = self._build_config()
        if config is None:
            return

        self.task_state.is_running = True
        self.task_state.current = 0
        self.task_state.total = 0
        self.task_state.message = ""
        self.task_state.success = 0
        self.task_state.failed.clear()
        if config.login_mode == "manual":
            self.task_state.error_message = (
                "브라우저에서 로그인한 뒤 계속 진행 버튼을 눌러주세요."
            )
            self._show_manual_login_window()
        else:
            self.task_state.error_message = ""
        self.refresh_task_state()

        Thread(target=self._run_upload, args=(config,), daemon=True).start()

    def _build_config(self) -> UploadConfig | None:
        if self.form_state.directory is None:
            self.task_state.error_message = "업로드 디렉토리를 선택해주세요."
            self.refresh_task_state()
            return None

        if self.form_state.login_mode == "auto":
            email = self.app_config.mattermost_email.strip()
            if not email:
                self.task_state.error_message = "저장된 Mattermost 이메일이 없습니다."
                self.refresh_task_state()
                return None

            if not self.auth_service.has_password(email):
                self.task_state.error_message = "저장된 Mattermost 비밀번호가 없습니다."
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
        self._manual_login_event = Event()
        uploader = Uploader(
            config=config,
            app_config=self.app_config,
            credentials=self.auth_service.repository,
            on_progress=self._handle_progress,
            wait_for_manual_login=(
                self._wait_for_manual_login_confirmation
                if config.login_mode == "manual"
                else None
            ),
        )
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
        self._close_manual_login_window()
        self.task_state.is_running = False
        self.task_state.success = result.success
        self.task_state.failed = list(result.failed)
        self.task_state.message = ""
        self.task_state.error_message = ""

        if result.success > 0:
            self._upload_succeeded = True
            self._mark_directory_uploaded(result.success_indices)

        self.refresh_task_state()

    def _mark_directory_uploaded(self, indices: list[int]) -> None:
        """업로드 성공 후 히스토리 엔트리에 성공한 조각 인덱스를 기록한다."""
        directory = self.form_state.directory
        if directory is None:
            return
        history_service = HistoryService()
        try:
            entry = history_service.resolve_from_directory(directory)
            history_service.mark_uploaded_indices(entry, indices)
        except Exception:  # noqa: BLE001
            pass  # split 없이 직접 디렉토리를 지정한 경우 — 무시

    def _finish_upload_error(self, message: str) -> None:
        self._close_manual_login_window()
        self.task_state.is_running = False
        self.task_state.message = ""
        self.task_state.error_message = message
        self.refresh_task_state()

    def _wait_for_manual_login_confirmation(self) -> None:
        if self._manual_login_event is None:
            raise RuntimeError("수동 로그인 대기 이벤트가 준비되지 않았습니다.")

        self.frame.after(0, self._show_manual_login_window)
        self._manual_login_event.wait()

    def _show_manual_login_window(self) -> None:
        if (
            self._manual_login_window is not None
            and self._manual_login_window.winfo_exists()
        ):
            self._manual_login_window.deiconify()
            self._manual_login_window.lift()
            self._manual_login_window.focus_force()
            return

        window = tk.Toplevel(self.frame)
        window.title("Mattermost 로그인 확인")
        window.resizable(False, False)

        ttk.Label(
            window,
            text="브라우저에서 Mattermost 로그인을 완료한 뒤\n아래 버튼을 눌러 업로드를 계속 진행하세요.",
            justify="center",
        ).pack(padx=20, pady=(20, 12))

        ttk.Button(
            window,
            text="로그인 완료, 계속 진행",
            command=self._confirm_manual_login,
        ).pack(pady=(0, 20))

        window.protocol("WM_DELETE_WINDOW", lambda: None)
        window.transient(self.frame.winfo_toplevel())
        window.grab_set()
        window.lift()
        window.focus_force()
        self._manual_login_window = window

    def _confirm_manual_login(self) -> None:
        if self._manual_login_event is not None:
            self._manual_login_event.set()
        self._close_manual_login_window()

    def _close_manual_login_window(self) -> None:
        if (
            self._manual_login_window is not None
            and self._manual_login_window.winfo_exists()
        ):
            self._manual_login_window.grab_release()
            self._manual_login_window.destroy()
        self._manual_login_window = None

    def _account_status_text(self) -> str:
        email = self.email_var.get().strip() or self.app_config.mattermost_email
        if not email:
            return "저장된 계정이 없습니다."

        if self.auth_service.has_password(email):
            return f"저장된 계정: {email}"

        return f"이메일만 저장됨: {email}"

    def _has_shareable_history_entry(self) -> bool:
        """현재 선택된 디렉토리가 이미 업로드되었고 아직 공유되지 않았는지 확인한다."""
        directory = self.form_state.directory
        if directory is None:
            return False

        history_service = HistoryService()
        try:
            entry = history_service.resolve_from_directory(directory)
        except Exception:  # noqa: BLE001
            return False

        return entry.uploaded and not entry.gallery_name

    # ── 갤러리 공유 ────────────────────────────────────────

    def _start_gallery_share(self) -> None:
        import tkinter.simpledialog as simpledialog

        author = simpledialog.askstring(
            "갤러리 공유",
            "작성자 이름을 입력하세요:",
            initialvalue="Anonymous",
            parent=self.frame.winfo_toplevel(),
        )
        if not author:
            return

        self._run_gallery_share(author=author)

    def _run_gallery_share(self, *, author: str = "Anonymous") -> None:
        if self.share_button is not None:
            self.share_button.configure(state="disabled")

        self.task_state.is_running = True
        self.task_state.current = 0
        self.task_state.total = 3
        self.task_state.message = "갤러리에 공유 준비 중..."
        self.task_state.error_message = ""
        self.refresh_task_state()

        Thread(
            target=self._gallery_share_worker,
            kwargs={"author": author},
            daemon=True,
        ).start()

    def _gallery_share_worker(self, *, author: str = "Anonymous") -> None:
        history_service = HistoryService()
        directory = self.form_state.directory
        try:
            if directory:
                entry = history_service.resolve_from_directory(directory)
            else:
                entry = history_service.get_latest()
                if entry is None:
                    raise HistoryNotFoundError("히스토리가 비어 있습니다.")
        except Exception as exc:  # noqa: BLE001
            self.frame.after(0, lambda e=str(exc): self._finish_share(e))
            return

        if not entry.uploaded:
            msg = "먼저 Mattermost에 업로드한 후 공유해주세요."
            self.frame.after(0, lambda m=msg: self._finish_share(m))
            return

        if entry.gallery_name:
            msg = f"이미 갤러리에 공유된 이모지입니다. (갤러리 이름: {entry.gallery_name})"
            self.frame.after(0, lambda m=msg: self._finish_share(m))
            return

        config = GalleryConfig(
            gallery_repo=self.app_config.gallery_repo,
            emoji_name=entry.emoji_name,
            input_path=Path(entry.input_path),
            output_dir=Path(entry.output_dir),
            cols=entry.cols,
            rows=entry.rows,
            tile_size=entry.tile_size,
            frame_step=entry.frame_step,
            tile_count=entry.tile_count,
            author=author,
        )

        try:
            result = GalleryService(config, on_progress=self._handle_progress).run()
        except GalleryAPIError as exc:
            msg = str(exc)
            self.frame.after(0, lambda m=msg: self._finish_share(m))
            return

        if result.success:
            history_service.mark_shared(entry, result.emoji_name)
            msg = f"공유 완료: {result.gallery_url}"
            self.frame.after(0, lambda m=msg: self._finish_share(m, shared=True))
        else:
            msg = f"공유 실패: {result.error_message}"
            self.frame.after(0, lambda m=msg: self._finish_share(m))

    def _finish_share(self, message: str, *, shared: bool = False) -> None:
        self.task_state.is_running = False
        self.task_state.message = ""
        self.task_state.error_message = message
        if shared:
            self._upload_succeeded = False  # 공유 완료 → 다시 share 불가
        self.refresh_task_state()
        if shared:
            messagebox.showinfo(
                "갤러리 공유 완료",
                message,
                parent=self.frame.winfo_toplevel(),
            )

    # ── 유틸 ─────────────────────────────────────────────

    def _failed_indices_text(self) -> str:
        if not self.task_state.failed:
            return "-"

        indices: list[str] = []
        for path, _reason in self.task_state.failed:
            match = self.FAILED_INDEX_RE.search(path.stem)
            if match:
                indices.append(match.group(1).lower())
            else:
                indices.append(path.stem)

        return ", ".join(indices)

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
