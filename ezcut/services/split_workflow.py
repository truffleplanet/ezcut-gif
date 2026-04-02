from datetime import datetime

from ezcut.repository.history import HistoryEntry
from ezcut.services.history import HistoryService
from ezcut.services.splitter import Splitter
from ezcut.store.models import SplitConfig, SplitResult
from ezcut.store.state import ProgressCallback


class SplitWorkflow:
    """분할 및 히스토리 저장을 포함한 전체 작업을 관리한다."""

    def __init__(
        self,
        config: SplitConfig,
        history_service: HistoryService | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self.history_service = history_service
        self.on_progress = on_progress

    def run(self) -> SplitResult:
        """분할을 실행하고 결과를 히스토리에 기록한다."""
        splitter = Splitter(self.config, on_progress=self.on_progress)
        result = splitter.run()

        if self.history_service is not None:
            self._record_history(result)

        return result

    def _record_history(self, result: SplitResult) -> None:
        """작업 결과를 히스토리에 저장한다."""
        if self.history_service is None:
            return
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            input_path=str(self.config.input_path),
            output_dir=str(result.output_dir),
            emoji_name=self.config.emoji_name or self.config.input_path.stem,
            cols=result.cols,
            rows=result.rows,
            tile_size=self.config.tile_size,
            frame_step=result.frame_step,
            tile_count=result.cols * result.rows,
        )
        self.history_service.add(entry)
