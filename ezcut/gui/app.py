import tkinter as tk
from pathlib import Path
from tkinter import ttk

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

    def run(self) -> None:
        self.root.mainloop()

    def _handle_split_complete(self, output_dir: Path) -> None:
        self.preview_task_state.selected_directory = output_dir
        self.preview_tab.set_directory(output_dir)
        self.upload_form_state.directory = output_dir
        self.upload_tab.set_directory(output_dir)
