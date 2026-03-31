from collections.abc import Callable

ProgressCallback = Callable[[int, int, str], None]
"""(현재값, 전체값, 메시지) 시그니처의 진행률 콜백."""
