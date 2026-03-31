from collections import Counter

from PIL import Image

from ezcut.store.models import PreviewConfig, Tile
from ezcut.utils.emoji_txt import parse_emoji_txt
from ezcut.utils.frames import load_first_frame


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
        grid = parse_emoji_txt(self.directory)
        self.rows = len(grid)
        self.cols = max(len(row) for row in grid)

        sizes: list[tuple[int, int]] = []
        tiles: list[Tile] = []

        for row_index, row_paths in enumerate(grid):
            for col_index, path in enumerate(row_paths):
                if not path.exists():
                    continue

                image = Image.open(path)
                frame, duration_ms = load_first_frame(image)
                sizes.append(frame.size)

                tiles.append(
                    Tile(
                        path=path,
                        row_index=row_index,
                        col_index=col_index,
                        image=image,
                        frame_index=0,
                        current_frame=frame,
                        current_duration_ms=duration_ms,
                        next_change_ms=duration_ms,
                    )
                )

        if not tiles:
            raise ValueError("유효한 GIF 타일을 불러오지 못했습니다.")

        tile_size = Counter(sizes).most_common(1)[0][0]
        for tile in tiles:
            if tile.current_frame.size != tile_size:
                tile.current_frame = tile.current_frame.resize(
                    tile_size, Image.Resampling.LANCZOS
                )

        self.tiles = tiles
        self.tile_size = tile_size

    def reset_tile(self, tile: Tile) -> None:
        """타일을 첫 프레임 상태로 되돌린다."""
        tile.image.close()
        tile.image = Image.open(tile.path)
        tile.frame_index = 0
        tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
        if tile.current_frame.size != self.tile_size:
            tile.current_frame = tile.current_frame.resize(
                self.tile_size, Image.Resampling.LANCZOS
            )
        tile.next_change_ms = tile.current_duration_ms

    def advance_tile(self, tile: Tile, event_time_ms: int) -> bool:
        """타일을 다음 프레임으로 진행한다."""
        try:
            tile.image.seek(tile.frame_index + 1)
        except EOFError:
            tile.next_change_ms = None
            return False

        tile.frame_index += 1
        tile.current_frame, tile.current_duration_ms = load_first_frame(tile.image)
        if tile.current_frame.size != self.tile_size:
            tile.current_frame = tile.current_frame.resize(
                self.tile_size, Image.Resampling.LANCZOS
            )
        tile.next_change_ms = event_time_ms + tile.current_duration_ms
        return True

    def reset_all(self) -> None:
        """모든 타일을 첫 프레임 상태로 되돌린다."""
        for tile in self.tiles:
            self.reset_tile(tile)

    def next_event_ms(self) -> int | None:
        """다음 프레임 전환 시각을 반환한다."""
        pending = [
            tile.next_change_ms
            for tile in self.tiles
            if tile.next_change_ms is not None
        ]
        if not pending:
            return None
        return min(pending)
