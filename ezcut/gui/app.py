import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ezcut.gui.history_tab import HistoryTab
from ezcut.gui.preview_tab import PreviewTab
from ezcut.gui.split_tab import SplitTab
from ezcut.gui.upload_tab import UploadTab
from ezcut.services.version import VersionService
from ezcut.store.state import (
    PreviewTaskState,
    SplitFormState,
    SplitTaskState,
    UploadFormState,
    UploadTaskState,
)


class EzcutApp:
    """Ezcut GUI 메인 앱."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ezcut")
        self.root.geometry("900x640")

        self.split_form_state = SplitFormState()
        self.split_task_state = SplitTaskState()
        self.preview_task_state = PreviewTaskState()
        self.upload_form_state = UploadFormState()
        self.upload_task_state = UploadTaskState()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.history_tab = HistoryTab(
            self.notebook,
            on_history_selected=self._handle_history_selected,
        )
        self.split_tab = SplitTab(
            self.notebook,
            form_state=self.split_form_state,
            task_state=self.split_task_state,
            on_split_complete=self._handle_split_complete,
        )
        self.preview_tab = PreviewTab(
            self.notebook,
            task_state=self.preview_task_state,
        )
        self.upload_tab = UploadTab(
            self.notebook,
            form_state=self.upload_form_state,
            task_state=self.upload_task_state,
        )

        self.notebook.add(self.split_tab.frame, text="Split")
        self.notebook.add(self.preview_tab.frame, text="Preview")
        self.notebook.add(self.upload_tab.frame, text="Upload")
        self.notebook.add(self.history_tab.frame, text="History")

        # ── 하단 상태바 (버전 및 업데이트) ──────────────────────
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side="bottom", fill="x", padx=5, pady=2)

        self.version_service = VersionService()
        current_v = self.version_service.get_current_version()

        self.v_label = ttk.Label(
            self.status_bar, text=f"v{current_v}", foreground="gray"
        )
        self.v_label.pack(side="left")

        self.update_label = ttk.Label(self.status_bar, text="", cursor="hand2")
        self.update_label.pack(side="right")
        self.update_label.bind("<Button-1>", lambda e: self._show_update_guide())

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 시작 시 업데이트 체크
        self._check_for_updates()

    def _on_tab_changed(self, event) -> None:
        # 탭을 전환할 때 히스토리 탭인 경우 목록을 새로고침
        selected_tab_id = self.notebook.select()
        if selected_tab_id == str(self.history_tab.frame):
            self.history_tab.refresh()

    def run(self) -> None:
        self.root.mainloop()

    def _handle_split_complete(self, output_dir: Path) -> None:
        self.preview_task_state.selected_directory = output_dir
        self.preview_tab.set_directory(output_dir)
        self.upload_form_state.directory = output_dir
        self.upload_tab.set_directory(output_dir)

    def _handle_history_selected(self, output_dir: Path) -> None:
        self.preview_task_state.selected_directory = output_dir
        self.preview_tab.set_directory(output_dir)
        self.upload_form_state.directory = output_dir
        self.upload_tab.set_directory(output_dir)

        # 불러오기 완료 시 업로드 탭 갱신 트리거 및 이동 피드백
        self.notebook.select(self.upload_tab.frame)

    def _check_for_updates(self) -> None:
        """실시간으로 업데이트를 체크하여 UI에 반영합니다."""
        is_available, latest = self.version_service.check_update()
        if is_available and latest:
            self.update_label.config(
                text=f"🚀 New version available: v{latest}",
                foreground="#007acc",  # 링크 느낌의 색상
            )

    def _show_update_guide(self) -> None:
        """업데이트 가이드 팝업을 표시합니다."""
        guide = (
            "설치 환경에 맞는 명령어를 터미널에서 실행하세요:\n\n"
            "1. uv (권장):\n   uv tool upgrade ezcut\n\n"
            "2. pipx:\n   pipx upgrade ezcut\n\n"
            "3. pip:\n   pip install --upgrade git+https://github.com/S-P-A-N/ezcut-gif.git"
        )
        messagebox.showinfo("Update Guide", guide)
