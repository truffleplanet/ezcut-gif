from math import gcd


def compute_grid(width: int, height: int) -> tuple[int, int]:
    """GCD 기반으로 cols, rows를 계산한다."""
    g = gcd(width, height)
    cols, rows = width // g, height // g
    return cols, rows


def resolve_grid(
    width: int,
    height: int,
    cols: int | None,
    rows: int | None,
    *,
    max_pieces: int,
) -> tuple[int, int]:
    """사용자 오버라이드를 반영하여 최종 (cols, rows)를 결정한다.

    Raises:
        ValueError: GCD 기반 그리드가 max_pieces를 초과할 때.
    """
    if cols and rows:
        return cols, rows
    if cols:
        piece_w = width / cols
        r = round(height / piece_w)
        return cols, max(r, 1)
    if rows:
        piece_h = height / rows
        c = round(width / piece_h)
        return max(c, 1), rows

    c, r = compute_grid(width, height)
    if c * r > max_pieces:
        raise ValueError(
            f"GCD 기반 그리드가 {c}x{r} ({c * r}개)로 너무 큽니다. "
            f"--cols 와 --rows 옵션으로 그리드를 직접 지정해주세요."
        )
    return c, r
