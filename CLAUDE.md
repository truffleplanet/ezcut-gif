# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**ezcut-gif**는 애니메이션 GIF를 N×M 그리드 타일로 분할하고, 미리보기하고, Mattermost 커스텀 이모지로 일괄 업로드하는 Python CLI/GUI 도구입니다. SSAFY Mattermost 서버(`meeting.ssafy.com`)를 주요 대상으로 합니다.

## 명령어

```bash
# 의존성 설치
uv sync

# pre-commit 훅 등록
uv run pre-commit install

# 린트 및 포맷 (자동 수정)
uv run ruff check --fix .
uv run ruff format .

# 린트 확인 (CI 모드 — 수정 없이 검사만)
uv run ruff check .
uv run ruff format --check .

# 전체 파일 pre-commit 실행 (ruff check --fix + ruff format)
uv run pre-commit run --all-files

# CLI 실행
uv run ezcut split input.gif --cols 8 --rows 4
uv run ezcut preview --last
uv run ezcut upload --last
uv run ezcut               # 인터랙티브 홈 메뉴

# GUI 실행
uv run ezcut-gui
```

## 아키텍처

4-레이어 구조이며, 의존 방향은 항상 **위 → 아래**만 허용됩니다.

```
Interface (cli/, gui/)  →  Service (services/)  →  Store/Repository/Utils
```

- **Interface는 Service와 Store(모델)만 사용** — Utils/Repository 직접 참조 금지
- **Store, Repository, Utils는 서로 참조하지 않음**

### 레이어별 역할

| 레이어 | 디렉토리 | 역할 |
|--------|----------|------|
| Store | `store/models.py` | Frozen dataclass 설정/결과 (`SplitConfig`, `SplitResult`, `Tile` 등) |
| Store | `store/state.py` | Mutable dataclass GUI 상태 (`SplitFormState`, `SplitTaskState` 등) |
| Utils | `utils/` | 순수 함수 (프레임 추출, 그리드 계산, 최적화, emoji.txt 파싱, 이름 정규화) |
| Repository | `repository/` | 영속성 (TOML 설정, keyring 자격증명, JSON 히스토리) |
| Services | `services/` | 비즈니스 로직 (`Splitter`, `Previewer`, `Uploader`) |
| CLI | `cli/` | Typer 앱 — 인터랙티브 홈 메뉴 + 서브커맨드 (split/preview/upload/history) |
| GUI | `gui/` | Tkinter 탭 UI (SplitTab, PreviewTab, UploadTab) |

### 핵심 패턴

**Frozen Config → Service**: 서비스는 `models.py`의 frozen dataclass를 받아 실행. GUI는 `state.py`의 mutable state로 폼 관리.

**Progress Callback**: `ProgressCallback = Callable[[int, int, str], None]` — `(current, total, message)`. Splitter/Uploader가 사용하며, CLI(Rich Progress)와 GUI(Tk label) 양쪽에서 동일하게 동작.

**2패스 최적화** (Splitter):
1. Pass 1: frame_step=1로 모든 타일 저장 → 최대 크기 타일 파악
2. Pass 2: 최악 타일 기준으로 최적 frame_step(2~10) 탐색 후 전체 재저장 (기본 제한: 512KB/타일)

**CLI 이중 모드**: 인자가 모두 주어지면 직접 실행, 빠진 인자가 있으면 questionary로 인터랙티브 프롬프트.

### 엔트리포인트

- `ezcut` CLI: `ezcut/cli/__init__.py` → `app()` (Typer). 서브커맨드 없으면 `_home_loop()`으로 화살표키 메뉴.
- `ezcut-gui` GUI: `ezcut/gui/__main__.py` → `EzcutApp().run()`. Tkinter + 3탭, 서비스는 백그라운드 스레드에서 실행.

### 타일 명명 규칙

`{prefix}-{row}{col}.gif` — 행은 `a`~`z`, 열은 zero-pad 숫자 (예: `emoji-a01.gif`)

**emoji.txt**: 출력 디렉토리에 생성되는 레이아웃 파일. preview/upload가 그리드 구조 파악에 사용.

```text
:emoji-a01::emoji-a02:...
:emoji-b01::emoji-b02:...
```

## 의존성

| 패키지 | 역할 |
|--------|------|
| Pillow ≥9.0 | GIF 프레임 추출, RGBA 컴포지팅, 리사이즈 |
| Typer ≥0.24.1 | CLI 프레임워크 |
| questionary ≥2.1.1 | 인터랙티브 CLI 프롬프트 |
| keyring ≥25.7.0 | Mattermost 자격증명 보안 저장 |
| Selenium ≥4.41.0 | Chrome 자동화 (Mattermost 업로드) |
| tkinter | 미리보기/GUI (Python 내장) |
| ruff ≥0.9 | 린터/포맷터 (dev) |

## 커밋 컨벤션

브랜치: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`
커밋 접두사: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`
