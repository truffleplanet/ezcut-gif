from pathlib import Path

from ezcut.repository.history import HistoryEntry, HistoryRepository
from ezcut.services.exceptions import HistoryNotFoundError


class HistoryService:
    """작업 히스토리 관리 및 조회를 담당하는 서비스."""

    def __init__(self, repository: HistoryRepository | None = None) -> None:
        self.repository = repository or HistoryRepository()

    def get_latest(self) -> HistoryEntry | None:
        """가장 최근의 히스토리 엔트리를 반환한다."""
        return self.repository.latest()

    def list_history(self, limit: int | None = None) -> list[HistoryEntry]:
        """히스토리 목록을 반환한다."""
        return self.repository.list(limit=limit)

    def resolve_last_path(self) -> Path:
        """가장 최근 작업의 출력 디렉토리 경로를 확인하여 반환한다.

        Returns:
            Path: 최근 작업의 출력 디렉토리 경로.

        Raises:
            HistoryNotFoundError: 히스토리가 비어 있거나 디렉토리를 찾을 수 없는 경우.
        """
        latest = self.get_latest()
        if latest is None:
            raise HistoryNotFoundError(
                "히스토리가 비어 있습니다. 먼저 split을 실행해주세요."
            )

        path = Path(latest.output_dir)
        if not path.is_dir():
            raise HistoryNotFoundError(f"최근 작업 디렉토리를 찾을 수 없습니다: {path}")

        return path

    def resolve_from_directory(self, directory: Path) -> HistoryEntry:
        """디렉토리 경로와 일치하는 히스토리 엔트리를 찾는다.

        Args:
            directory: 찾고자 하는 출력 디렉토리 경로.

        Returns:
            HistoryEntry: 일치하는 히스토리 엔트리.

        Raises:
            HistoryNotFoundError: 히스토리에 해당 디렉토리가 없거나 디렉토리가 존재하지 않는 경우.
        """
        if not directory.is_dir():
            raise HistoryNotFoundError(f"디렉토리를 찾을 수 없습니다: {directory}")

        resolved = str(directory.resolve())
        for entry in self.list_history():
            if str(Path(entry.output_dir).resolve()) == resolved:
                return entry

        raise HistoryNotFoundError(
            f"히스토리에서 해당 디렉토리를 찾을 수 없습니다: {directory}"
        )

    def add(self, entry: HistoryEntry) -> None:
        """히스토리에 새 엔트리를 추가한다."""
        self.repository.add(entry)

    def mark_uploaded(self, entry: HistoryEntry) -> None:
        """엔트리를 Mattermost 업로드됨으로 표시한다."""
        self.repository.mark_uploaded(entry)

    def mark_shared(self, entry: HistoryEntry, gallery_name: str) -> None:
        """엔트리를 갤러리 공유됨으로 표시한다."""
        self.repository.mark_shared(entry, gallery_name)
