import tkinter as tk
from pathlib import Path
from tkinter import ttk

from ezcut.gui.history_tab import HistoryTab
from ezcut.gui.preview_tab import PreviewTab
from ezcut.gui.split_tab import SplitTab
from ezcut.gui.upload_tab import UploadTab
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

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

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
