from ezcut.store.models import PreviewConfig, Tile


class Previewer:
    """타일 미리보기 상태를 관리하는 서비스."""

    def __init__(self, config: PreviewConfig) -> None:
        self.config = config
        self.directory = config.directory
        self.tiles: list[Tile] = []
        self.rows = 0
        self.cols = 0
        self.tile_size: tuple[int, int] = (0, 0)

    @property
    def grid_info(self) -> tuple[int, int, tuple[int, int]]:
        """행, 열, 타일 크기 정보를 반환한다."""
        return self.rows, self.cols, self.tile_size

    def load(self) -> None:
        """emoji.txt와 타일 GIF를 불러온다."""
        raise NotImplementedError

    def reset_tile(self, tile: Tile) -> None:
        """타일을 첫 프레임 상태로 되돌린다."""
        raise NotImplementedError

    def advance_tile(self, tile: Tile, event_time_ms: int) -> bool:
        """타일을 다음 프레임으로 진행한다."""
        raise NotImplementedError

    def reset_all(self) -> None:
        """모든 타일을 첫 프레임 상태로 되돌린다."""
        raise NotImplementedError

    def next_event_ms(self) -> int | None:
        """다음 프레임 전환 시각을 반환한다."""
        raise NotImplementedError
