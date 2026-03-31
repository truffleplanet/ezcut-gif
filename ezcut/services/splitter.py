import itertools
from datetime import datetime
from pathlib import Path

from PIL import Image

from ..repository.history import HistoryEntry, HistoryRepository
from ..store.models import SplitConfig, SplitResult
from ..store.state import ProgressCallback
from ..utils.emoji_txt import write_emoji_txt
from ..utils.frames import extract_frames
from ..utils.grid import resolve_grid
from ..utils.naming import normalize_emoji_name, piece_id
from ..utils.optimize import apply_frame_step, find_optimal_step, save_piece


class Splitter:
    """GIF를 N×M 그리드 타일로 분할하는 서비스."""

    def __init__(
        self,
        config: SplitConfig,
        history: HistoryRepository | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self._config = config
        self._history = history
        self._progress = on_progress

    def run(self) -> SplitResult:
        """분할 파이프라인을 실행하고 결과를 반환한다."""
        cfg = self._config

        im = self._open_and_validate()

        width, height = im.size
        cols, rows = resolve_grid(
            width, height, cfg.cols, cfg.rows, max_pieces=cfg.max_pieces
        )
        if rows > 26:
            raise ValueError(
                f"행 수가 26을 초과합니다 ({rows}행). a-z로 표현할 수 없습니다."
            )

        output_dir = cfg.output_dir or Path(f"{cfg.input_path.stem}_pieces")
        emoji_name = normalize_emoji_name(cfg.emoji_name or cfg.input_path.stem)
        output_dir.mkdir(parents=True, exist_ok=True)

        self._report(0, 4, "프레임 추출 중...")
        frames = extract_frames(im)
        loop = im.info.get("loop", 0)

        self._report(1, 4, "타일 크롭 중...")
        piece_w = width // cols
        piece_h = height // rows
        col_pad = len(str(cols))

        cropped_tiles: list[list[tuple[Image.Image, int]]] = []
        filenames: list[str] = []

        for row, col in itertools.product(range(rows), range(cols)):
            x0, y0 = col * piece_w, row * piece_h
            box = (x0, y0, x0 + piece_w, y0 + piece_h)
            crop_frames = [
                (full_frame.crop(box), duration) for full_frame, duration in frames
            ]
            cropped_tiles.append(crop_frames)
            filenames.append(f"{emoji_name}-{piece_id(row, col, col_pad)}.gif")

        self._report(2, 4, "타일 저장 중 (Pass 1)...")
        frame_step = self._save_optimized(cropped_tiles, filenames, output_dir, loop)

        self._report(3, 4, "완료 처리 중...")
        emoji_txt_path = write_emoji_txt(
            output_dir=output_dir,
            emoji_name=emoji_name,
            rows=rows,
            cols=cols,
            piece_id_factory=lambda row, col: piece_id(row, col, col_pad),
        )

        if self._history is not None:
            self._history.add(
                HistoryEntry(
                    timestamp=datetime.now().isoformat(timespec="seconds"),
                    input_path=str(cfg.input_path),
                    output_dir=str(output_dir),
                    emoji_name=emoji_name,
                    cols=cols,
                    rows=rows,
                    tile_size=cfg.tile_size,
                    frame_step=frame_step,
                    tile_count=cols * rows,
                )
            )

        self._report(4, 4, "완료")

        return SplitResult(
            output_dir=output_dir,
            filenames=filenames,
            cols=cols,
            rows=rows,
            frame_step=frame_step,
            emoji_txt_path=emoji_txt_path,
        )

    def _open_and_validate(self) -> Image.Image:
        """입력 파일 존재 여부와 GIF 포맷을 검증하고 Image를 반환한다."""
        path = self._config.input_path
        if not path.is_file():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

        im = Image.open(path)
        if im.format != "GIF":
            raise ValueError(f"GIF 파일이 아닙니다: {path}")
        return im

    def _save_optimized(
        self,
        cropped_tiles: list[list[tuple[Image.Image, int]]],
        filenames: list[str],
        output_dir: Path,
        loop: int,
    ) -> int:
        """2패스 최적화로 타일을 저장하고 최종 frame_step을 반환한다."""
        target_size = self._config.tile_size
        max_file_size = self._config.max_file_size_kb * 1024
        speed_multiplier = self._config.speed_multiplier
        total = len(cropped_tiles)

        worst_idx = 0
        worst_size = 0

        for idx, (crop_frames, filename) in enumerate(zip(cropped_tiles, filenames)):
            images, durations = apply_frame_step(
                crop_frames,
                target_size,
                1,
                speed_multiplier=speed_multiplier,
            )
            path = output_dir / filename
            save_piece(images, durations, path, loop)
            size = path.stat().st_size
            if size > worst_size:
                worst_size = size
                worst_idx = idx
            self._report(idx + 1, total, f"Pass 1: {filename}")

        if worst_size <= max_file_size:
            return 1

        best_step = find_optimal_step(
            cropped_tiles[worst_idx],
            target_size,
            max_file_size,
            loop,
            speed_multiplier=speed_multiplier,
        )

        for idx, (crop_frames, filename) in enumerate(zip(cropped_tiles, filenames)):
            images, durations = apply_frame_step(
                crop_frames,
                target_size,
                best_step,
                speed_multiplier=speed_multiplier,
            )
            path = output_dir / filename
            save_piece(images, durations, path, loop)
            self._report(idx + 1, total, f"Pass 2: {filename}")

        return best_step

    def _report(self, current: int, total: int, message: str) -> None:
        if self._progress is not None:
            self._progress(current, total, message)
