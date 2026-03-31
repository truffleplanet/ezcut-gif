from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

HISTORY_DIR = Path.home() / ".config" / "ezcut"
HISTORY_FILE = HISTORY_DIR / "history.json"
MAX_HISTORY = 50


@dataclass(slots=True)
class HistoryEntry:
    # 작업 기본정보
    timestamp: str
    input_path: str
    output_dir: str
    emoji_name: str

    # split 결과정보
    cols: int
    rows: int
    tile_size: int
    frame_step: int
    tile_count: int


class HistoryRepository:
    def __init__(
        self,
        history_file: Path = HISTORY_FILE,
        max_history: int = MAX_HISTORY,
    ) -> None:
        self.history_file = history_file
        self.history_dir = history_file.parent
        self.max_history = max_history

    def add(self, entry: HistoryEntry) -> None:
        entries = self.list()
        entries.insert(0, entry)
        entries = entries[: self.max_history]

        self.history_dir.mkdir(parents=True, exist_ok=True)
        payload = [asdict(item) for item in entries]
        self.history_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list(self, limit: int | None = None) -> list[HistoryEntry]:
        if not self.history_file.exists():
            return []

        with self.history_file.open("r", encoding="utf-8") as file:
            raw_entries = json.load(file)

        entries = [HistoryEntry(**item) for item in raw_entries]
        if limit is None:
            return entries
        return entries[:limit]

    def latest(self) -> HistoryEntry | None:
        entries = self.list(limit=1)
        if not entries:
            return None
        return entries[0]
