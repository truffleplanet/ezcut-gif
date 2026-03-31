from PIL import Image


def extract_frames(im: Image.Image) -> list[tuple[Image.Image, int]]:
    """GIF의 모든 프레임을 RGBA 컴포지팅하여 (frame, duration_ms) 리스트로 반환.

    disposal method 0(기본), 2(배경 복원), 3(이전 프레임 복원)을 처리한다.
    """
    frames: list[tuple[Image.Image, int]] = []
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    n_frames = getattr(im, "n_frames", 1)

    for i in range(n_frames):
        im.seek(i)
        duration = im.info.get("duration", 100)
        disposal = im.disposal_method if hasattr(im, "disposal_method") else 0

        frame = im.convert("RGBA")

        if disposal == 2:
            temp_canvas = canvas.copy()
            temp_canvas.paste(frame, (0, 0), frame)
            frames.append((temp_canvas.copy(), duration))
            canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
        elif disposal == 3:
            prev_canvas = canvas.copy()
            canvas.paste(frame, (0, 0), frame)
            frames.append((canvas.copy(), duration))
            canvas = prev_canvas
        else:
            canvas.paste(frame, (0, 0), frame)
            frames.append((canvas.copy(), duration))

    return frames


def load_first_frame(image: Image.Image) -> tuple[Image.Image, int]:
    """GIF 첫 프레임을 RGBA로 변환하여 (frame, duration_ms) 반환.

    duration은 최소 20ms를 보장한다.
    """
    frame = image.convert("RGBA").copy()
    duration_ms = max(20, int(image.info.get("duration", 30)))
    return frame, duration_ms
