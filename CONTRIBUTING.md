# Contributing

ezcut에 기여해주셔서 감사합니다! 이 문서는 개발 환경 설정부터 PR 제출까지의 과정을 안내합니다.

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- Google Chrome (업로드 기능 테스트 시 필요)

## 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/S-P-A-N/ezcut-gif.git
cd ezcut-gif

# 의존성 설치 및 가상환경 구성
uv sync

# pre-commit 훅 등록 (커밋 시 자동 린트/포맷)
uv run pre-commit install
```

## 코드 스타일

본 프로젝트는 [Ruff](https://docs.astral.sh/ruff/)를 사용하여 린트와 포맷을 관리합니다. pre-commit 훅이 등록되어 있으면 커밋 시 자동으로 검사됩니다.

```bash
# 가장 권장하는 방법: pre-commit으로 전체 파일 검사
uv run pre-commit run --all-files

# 또는 개별 실행
uv run ruff format .        # 포맷팅
uv run ruff check --fix .   # 린트 자동 수정 및 임포트 정렬
```

CI에서도 동일한 검사가 실행됩니다 (`ruff check` + `ruff format --check`).

### 코딩 컨벤션 및 개발 규칙

1. **절대 경로 임포트(Absolute Imports) 지향**:
   프로젝트 내부 모듈을 참조할 때는 되도록 최상위 패키지 기준의 절대 경로를 사용합니다. 
   - ⭕ 권장: `from ezcut.services.history import HistoryEntry`
   - ❌ 지양: `from ..services.history import HistoryEntry` (단, 동일 폴더 내의 매우 짧은 상대 경로는 예외적으로 허용)

2. **타입 힌트(Type Hinting) 의무화**:
   가독성과 안전성을 위해 함수의 모든 매개변수와 반환값에 Python 타입 힌트를 반드시 명시합니다.

3. **관심사 분리 (Separation of Concerns)**:
   인터페이스 계층(`CLI`, `GUI`)에는 절대 복잡한 비즈니스 로직(예: IO 작업, 통신)을 포함하지 말고, 반드시 `services` 영역으로 분리하여 호출합니다.

4. **상태 관리 구조와 불변성**:
   핵심 데이터 모델이나 설정 등은 가급적 `frozen=True` 옵션이 켜진 `dataclasses`를 사용하여 설계합니다.

## 프로젝트 구조

```text
ezcut/
├── cli/          # Typer CLI (split, preview, upload, history 서브커맨드)
├── gui/          # Tkinter GUI (탭: Split, Preview, Upload)
├── services/     # 비즈니스 로직 (Splitter, Previewer, Uploader)
├── store/        # 데이터 모델 (SplitConfig, UploadConfig 등 frozen dataclass)
├── repository/   # 영속성 (ConfigRepository → TOML, CredentialRepository → keyring)
└── utils/        # 순수 함수 (frames, grid, optimize, emoji_txt, naming)
```

### 의존성 규칙

- **상위 → 하위만 허용**: Interface(cli/gui) → Service → Store/Repository/Utils
- Store, Repository, Utils는 서로 참조하지 않음
- Interface는 Service와 Store(모델)만 사용, Utils/Repository 직접 참조 금지

자세한 아키텍처는 [ARCHITECTURE.md](ARCHITECTURE.md)를 참고하세요.

## 로컬 실행

```bash
# CLI 실행
uv run ezcut split input.gif --cols 8 --rows 4

# GUI 실행
uv run ezcut-gui

# 모듈로 실행
uv run python -m ezcut split input.gif
```

## 브랜치 & 커밋 컨벤션

### 브랜치 이름

```text
feat/기능-설명
fix/버그-설명
refactor/대상-설명
chore/작업-설명
```

### 커밋 메시지 (Conventional Commits)

본 프로젝트는 **Release Please**를 사용하여 자동으로 버전을 올리고 변경 로그를 작성합니다. 따라서 아래 컨벤션을 **반드시** 준수해야 합니다.

```text
feat: 새로운 기능 추가 (Minor 버전 업)
fix: 버그 수정 (Patch 버전 업)
docs: 문서 수정 (Patch 버전 업 가능)
chore: 빌드, 설정 등 기타 변경
refactor: 코드 구조 변경
perf: 성능 개선
```

- **Minor 업**: `feat: ...`
- **Patch 업**: `fix: ...`, `docs: ...` 등
- **Major 업**: 메시지 바디에 `BREAKING CHANGE:`를 포함하거나 `feat!: ...` 처럼 느낌표를 추가하세요.

## 버전 관리 및 릴리스

1. **VCS 기반 버전 (`hatch-vcs`)**: 프로젝트 버전은 `pyproject.toml`에 고정되어 있지 않고 Git Tag를 기반으로 동적으로 결정됩니다. 로컬 개발 시에는 `uv run hatch version`으로 현재 버전을 확인할 수 있습니다.
2. **자동 릴리스 프로세스**:
   - `main` 브랜치에 머지된 커밋 메시지를 바탕으로 **Release Please**가 자동으로 릴리스 PR을 생성합니다.
   - 해당 PR이 머지되면 자동으로 GitHub Release가 생성되고 Git Tag가 생성됩니다.
   - 이 과정에서 별도의 버전 번호 수동 수정은 필요하지 않습니다.

## Pull Request

1. `main` 브랜치에서 새 브랜치를 생성합니다.
2. 작업 완료 후 PR을 올립니다 — [PR 템플릿](.github/PULL_REQUEST_TEMPLATE.md)을 따라주세요.
3. **중요**: PR의 제목이나 머지될 커밋 메시지가 위 컨벤션(`feat:`, `fix:` 등)을 따라야 버전에 정상 반영됩니다.
4. CI 린트가 통과해야 머지 가능합니다.

## 이슈

버그 리포트와 기능 제안은 [이슈 템플릿](.github/ISSUE_TEMPLATE/)을 사용해주세요.
