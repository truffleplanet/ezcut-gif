import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image


def apply_frame_step(
    crop_frames: list[tuple[Image.Image, int]],
    target_size: int,
    frame_step: int,
    speed_multiplier: float = 1.0,
) -> tuple[list[Image.Image], list[int]]:
    """프레임 스킵을 적용하여 (images, durations) 반환.

    duration은 최소 20ms를 보장하고, 스킵 비율만큼 곱한다.
    """
    durations = [max(dur, 20) for _, dur in crop_frames]
    images = [
        f.resize((target_size, target_size), Image.LANCZOS) for f, _ in crop_frames
    ]

    if frame_step > 1:
        images = images[::frame_step]
        durations = [d * frame_step for d in durations[::frame_step]]

    if speed_multiplier != 1.0:
        min_duration = 40
        durations = [
            max(min_duration, int(round(duration / speed_multiplier)))
            for duration in durations
        ]

    return images, durations


def save_piece(
    images: list[Image.Image],
    durations: list[int],
    output: Path | BinaryIO,
    loop: int,
) -> None:
    """이미지 시퀀스를 GIF로 저장. output은 파일 경로 또는 file-like 객체."""
    if len(images) == 1:
        images[0].save(output, format="GIF")
    else:
        images[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=loop,
            disposal=2,
        )


def find_optimal_step(
    crop_frames: list[tuple[Image.Image, int]],
    target_size: int,
    max_file_size: int,
    loop: int,
    speed_multiplier: float = 1.0,
) -> int:
    """크기 제한을 만족하는 최소 frame_step을 찾는다.

    BytesIO로 인메모리 측정하므로 디스크 I/O 없음.
    맞는 step이 없으면 마지막으로 테스트한 값(10)을 반환한다.
    """
    for step in range(2, 11):
        images, durations = apply_frame_step(
            crop_frames,
            target_size,
            step,
            speed_multiplier=speed_multiplier,
        )
        buf = io.BytesIO()
        save_piece(images, durations, buf, loop)
        if buf.tell() <= max_file_size:
            return step

    return 10
