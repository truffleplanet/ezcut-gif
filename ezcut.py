import argparse
import itertools
import os
import string
import sys
from math import gcd

from PIL import Image

MAX_PIECES = 10000
MAX_FILE_SIZE = 512 * 1024  # 512KB


def parse_args():
    parser = argparse.ArgumentParser(
        description="GIF 파일을 그리드로 분할하여 각 조각을 개별 GIF로 저장합니다."
    )
    parser.add_argument("input", help="입력 GIF 파일 경로")
    parser.add_argument(
        "-s", "--size", type=int, default=128,
        help="출력 조각 크기 (정사각형, 기본: 128)",
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="출력 디렉토리 (기본: {입력파일명}_pieces/)",
    )
    parser.add_argument("--cols", type=int, default=None, help="그리드 열 수 (수동 지정)")
    parser.add_argument("--rows", type=int, default=None, help="그리드 행 수 (수동 지정)")
    parser.add_argument(
        "-n", "--name", default=None,
        help="이모지 베이스 이름 (기본: 입력파일명). 이모지 텍스트 파일 생성에 사용",
    )
    return parser.parse_args()


def compute_grid(width, height):
    g = gcd(width, height)
    cols, rows = width // g, height // g
    return cols, rows


def resolve_grid(width, height, cols_override, rows_override):
    if cols_override and rows_override:
        return cols_override, rows_override
    if cols_override:
        piece_w = width / cols_override
        rows = round(height / piece_w)
        return cols_override, max(rows, 1)
    if rows_override:
        piece_h = height / rows_override
        cols = round(width / piece_h)
        return max(cols, 1), rows_override

    cols, rows = compute_grid(width, height)
    if cols * rows > MAX_PIECES:
        sys.exit(
            f"Error: GCD 기반 그리드가 {cols}x{rows} ({cols * rows}개)로 너무 큽니다.\n"
            f"  --cols 와 --rows 옵션으로 그리드를 직접 지정해주세요."
        )
    return cols, rows


def extract_frames(im):
    frames = []
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


def save_piece(images, durations, output_path, loop, colors):
    if colors < 256:
        quantized = [im.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
                     for im in images]
    else:
        quantized = images

    if len(quantized) == 1:
        quantized[0].save(output_path, format="GIF")
    else:
        quantized[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=quantized[1:],
            duration=durations,
            loop=loop,
            disposal=2,
        )


def apply_strategy(crop_frames, target_size, colors, frame_step):
    durations = [max(dur, 20) for _, dur in crop_frames]
    images = [f.resize((target_size, target_size), Image.LANCZOS)
              for f, _ in crop_frames]

    if frame_step > 1:
        images = images[::frame_step]
        durations = [d * frame_step for d in durations[::frame_step]]

    return images, durations


def build_strategies():
    # 1) 원본 (256색)
    # 2) 128색
    # 3) 128색 + 프레임 스킵 2, 3, 4, ...
    strategies = [(256, 1), (128, 1)]
    for step in range(2, 11):
        strategies.append((128, step))
    return strategies


def _strategy_label(colors, frame_step):
    label = f"{colors}colors"
    if frame_step > 1:
        label += f", frame 1/{frame_step}"
    return label


def find_strategy(pieces_crop_frames, output_dir, filenames, loop, target_size):
    strategies = build_strategies()
    total = len(pieces_crop_frames)
    import tempfile

    # 1단계: 원본(256색)으로 전부 저장하면서 최악 조각 찾기
    print("  Pass 1: saving raw...")
    worst_idx = 0
    worst_size = 0
    colors, frame_step = strategies[0]
    for idx, (crop_frames, filename) in enumerate(zip(pieces_crop_frames, filenames)):
        images, durations = apply_strategy(crop_frames, target_size, colors, frame_step)
        path = os.path.join(output_dir, filename)
        save_piece(images, durations, path, loop, colors)
        size = os.path.getsize(path)
        if size > worst_size:
            worst_size = size
            worst_idx = idx
        print(f"\r    [{idx + 1}/{total}] {filename}", end="", flush=True)
    print()

    if worst_size <= MAX_FILE_SIZE:
        print(f"  -> {_strategy_label(colors, frame_step)} OK (max {worst_size // 1024}KB)")
        return

    print(f"  -> max {worst_size // 1024}KB, need optimization...")

    # 2단계: 최악 조각으로 전략 탐색
    worst_crop = pieces_crop_frames[worst_idx]
    tmp_path = os.path.join(output_dir, "_test.gif")
    best_strategy = strategies[-1]

    for colors, frame_step in strategies[1:]:
        images, durations = apply_strategy(worst_crop, target_size, colors, frame_step)
        save_piece(images, durations, tmp_path, loop, colors)
        size = os.path.getsize(tmp_path)
        label = _strategy_label(colors, frame_step)
        if size <= MAX_FILE_SIZE:
            print(f"  -> {label} fits worst piece ({size // 1024}KB)")
            best_strategy = (colors, frame_step)
            break
        print(f"  -> {label}: {size // 1024}KB, still over")

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    # 3단계: 선택된 전략으로 전체 저장
    colors, frame_step = best_strategy
    label = _strategy_label(colors, frame_step)
    print(f"  Pass 2: saving all with {label}...")
    for idx, (crop_frames, filename) in enumerate(zip(pieces_crop_frames, filenames)):
        images, durations = apply_strategy(crop_frames, target_size, colors, frame_step)
        path = os.path.join(output_dir, filename)
        save_piece(images, durations, path, loop, colors)
        print(f"\r    [{idx + 1}/{total}] {filename}", end="", flush=True)
    print()


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"Error: 파일을 찾을 수 없습니다: {args.input}")

    im = Image.open(args.input)
    if im.format != "GIF":
        sys.exit(f"Error: GIF 파일이 아닙니다: {args.input}")

    width, height = im.size
    cols, rows = resolve_grid(width, height, args.cols, args.rows)

    if rows > 26:
        sys.exit(f"Error: 행 수가 26을 초과합니다 ({rows}행). a-z로 표현할 수 없습니다.")

    piece_w = width // cols
    piece_h = height // rows

    output_dir = args.output_dir
    if output_dir is None:
        stem = os.path.splitext(os.path.basename(args.input))[0]
        output_dir = f"{stem}_pieces"

    emoji_name = args.name
    if emoji_name is None:
        emoji_name = os.path.splitext(os.path.basename(args.input))[0]

    print(f"Input: {width}x{height}, Grid: {cols}x{rows}, "
          f"Piece: {piece_w}x{piece_h} -> {args.size}x{args.size}")

    frames = extract_frames(im)
    loop = im.info.get("loop", 0)

    os.makedirs(output_dir, exist_ok=True)

    col_pad = len(str(cols))

    def piece_id(row, col):
        return f"{string.ascii_lowercase[row]}{col + 1:0{col_pad}d}"

    # 모든 조각의 크롭 프레임 준비
    print("Cropping pieces...")
    pieces_crop_frames = []
    filenames = []
    for row, col in itertools.product(range(rows), range(cols)):
        x0 = col * piece_w
        y0 = row * piece_h
        box = (x0, y0, x0 + piece_w, y0 + piece_h)
        crop_frames = [(full_frame.crop(box), duration)
                       for full_frame, duration in frames]
        pieces_crop_frames.append(crop_frames)
        filenames.append(f"{emoji_name}-{piece_id(row, col)}.gif")

    # 최적 전략 탐색 + 저장
    find_strategy(pieces_crop_frames, output_dir, filenames, loop, args.size)

    # 이모지 텍스트 생성
    emoji_lines = []
    for row in range(rows):
        line = ""
        for col in range(cols):
            line += f":{emoji_name}-{piece_id(row, col)}:"
        emoji_lines.append(line)

    emoji_path = os.path.join(output_dir, "emoji.txt")
    with open(emoji_path, "w", encoding="utf-8") as f:
        f.write("\n".join(emoji_lines) + "\n")

    total = cols * rows
    print(f"Done. {total} pieces saved to {output_dir}/")
    print(f"Emoji text saved to {emoji_path}")


if __name__ == "__main__":
    main()
