import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from ezcut.services.history import HistoryService


class HistoryTab:
    """히스토리 탭 UI를 구성한다."""

    def __init__(
        self,
        parent: tk.Widget,
        on_history_selected: Callable[[Path], None] | None = None,
    ) -> None:
        self.on_history_selected = on_history_selected
        self.frame = ttk.Frame(parent, padding=16)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        ttk.Label(self.frame, text="History", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self.frame,
            text="과거 분할 및 업로드 내역을 확인하고 작업 대상으로 불러올 수 있습니다.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        # 트리 구성
        self.tree = ttk.Treeview(
            self.frame,
            columns=("name", "grid", "date", "up", "share", "dir"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("name", text="이름")
        self.tree.heading("grid", text="조각")
        self.tree.heading("date", text="일시")
        self.tree.heading("up", text="업로드")
        self.tree.heading("share", text="공유")
        self.tree.heading("dir", text="출력 경로")

        self.tree.column("name", width=120)
        self.tree.column("grid", width=60, anchor="center")
        self.tree.column("date", width=140, anchor="center")
        self.tree.column("up", width=60, anchor="center")
        self.tree.column("share", width=60, anchor="center")
        self.tree.column("dir", width=300)

        self.tree.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_double_click)

        actions = ttk.Frame(self.frame)
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))

        ttk.Button(actions, text="새로고침", command=self.refresh).pack(side="left")

        self.select_button = ttk.Button(
            actions, text="이 항목 불러오기", command=self._on_select_button
        )
        self.select_button.pack(side="right")

        self.status_var = tk.StringVar(value="")
        ttk.Label(actions, textvariable=self.status_var).pack(
            side="right", padx=(0, 16)
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self._on_selection_changed(None)

        self.refresh()

    def refresh(self, *_args) -> None:
        """히스토리 목록을 다시 불러온다."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        history_service = HistoryService()
        entries = history_service.list_history()

        for entry in entries:
            up_mark = "✔" if entry.uploaded else "-"
            share_mark = "🔗" if entry.gallery_name else "-"
            self.tree.insert(
                "",
                "end",
                values=(
                    entry.emoji_name,
                    f"{entry.cols}x{entry.rows}",
                    entry.timestamp[:19],
                    up_mark,
                    share_mark,
                    entry.output_dir,
                ),
            )

    def _on_selection_changed(self, _event) -> None:
        selected = self.tree.selection()
        if selected:
            self.select_button.configure(state="normal")
        else:
            self.select_button.configure(state="disabled")

    def _on_double_click(self, _event) -> None:
        self._notify_selected()

    def _on_select_button(self) -> None:
        self._notify_selected()

    def _notify_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item.get("values")
        if not values or len(values) < 6:
            return

        output_dir = values[5]
        if self.on_history_selected is not None:
            self.on_history_selected(Path(output_dir))

        self.status_var.set("불러오기 완료!")
        self.frame.after(3000, lambda: self.status_var.set(""))
