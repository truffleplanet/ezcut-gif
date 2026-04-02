# ezcut CLI 가이드

## 목차

- [실행 방법](#실행-방법)
- [인터랙티브 모드](#인터랙티브-모드)
- [`ezcut split` - GIF 분할](#ezcut-split---gif-분할)
- [`ezcut preview` - 미리보기](#ezcut-preview---미리보기)
- [`ezcut upload` - Mattermost 업로드](#ezcut-upload---mattermost-업로드)
- [`ezcut share` - 갤러리 공유](#ezcut-share---갤러리-공유)
- [`ezcut history` - 작업 히스토리](#ezcut-history---작업-히스토리)
- [전체 워크플로 예시](#전체-워크플로-예시)
- [경로 및 명령 점검 메모](#경로-및-명령-점검-메모)

`ezcut` CLI는 GIF 분할, 미리보기, 업로드, 히스토리 조회를 터미널에서 수행할 수 있는 명령줄 인터페이스입니다.

## 실행 방법

설치 후에는 아래처럼 바로 실행할 수 있습니다.

```bash
ezcut
```

소스 저장소를 직접 실행하는 경우에는 프로젝트 루트에서 아래처럼 사용할 수 있습니다.

```bash
uv sync
uv run ezcut
```

서브커맨드를 직접 실행할 때도 같은 방식으로 사용할 수 있습니다.

```bash
ezcut split ./input.gif
ezcut preview --last
ezcut upload --last
ezcut history
```

소스 저장소에서는 다음과 같이 실행합니다.

```bash
uv run ezcut split ./input.gif
uv run ezcut preview --last
uv run ezcut upload --last
uv run ezcut history
```

## 인터랙티브 모드

인자 없이 `ezcut`만 실행하면 화살표 키로 동작을 선택할 수 있는 인터랙티브 홈 메뉴가 표시됩니다.

```bash
ezcut
```

각 명령어도 필수 인자를 생략하면 위자드나 대화형 프롬프트가 단계별로 안내합니다. 또한 각 선택 깊이에서 **`Ctrl+C` (또는 `Esc`)** 키를 통해 언제든 안전하게 현재 선택(위자드)을 취소하고 홈 메뉴로 뒤로 무를 수 있습니다.

## `ezcut split` - GIF 분할

```bash
ezcut split <GIF 파일> [옵션]
```

GIF 파일을 N×M 그리드로 분할하여 각 조각을 개별 GIF로 저장합니다.

인자를 생략하면 위자드가 안내합니다.

### 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--cols`, `-c` | 가로 조각 수 | GIF 비율에 맞춰 자동 계산 |
| `--rows`, `-r` | 세로 조각 수 | GIF 비율에 맞춰 자동 계산 |
| `--size`, `-s` | 타일 크기 (px) | `128` |
| `--max-size` | 타일 최대 파일 크기 (KB) | `512` |
| `--output-dir`, `-o` | 출력 디렉토리 | `./{파일명}_pieces` |
| `--name`, `-n` | 이모지 베이스 이름 | 파일명 |
| `--speed` | 배속 (1.0 = 원본) | `1.0` |

### 예시

```bash
# 16x9 그리드로 분할, 이모지 이름 지정
ezcut split ./input.gif --cols 16 --rows 9 --name my-emoji

# 타일 크기 64px, 최대 256KB 제한
ezcut split ./input.gif --size 64 --max-size 256

# 출력 디렉토리 직접 지정
ezcut split ./input.gif --output-dir ./output_pieces
```

### 출력 결과

분할이 완료되면 출력 디렉토리에 타일 GIF와 `emoji.txt` 파일이 생성됩니다.

```text
output_pieces/
├── my-emoji-a01.gif
├── my-emoji-a02.gif
├── ...
├── my-emoji-i16.gif
└── emoji.txt
```

`emoji.txt`는 미리보기와 업로드에서 그리드 구조를 파악할 때 사용됩니다.

타일 파일명 규칙은 아래와 같습니다.

```text
{이름}-{행}{열}.gif
```

- 행: `a` ~ `z`
- 열: `01`, `02`, `03`, ...

## `ezcut preview` - 미리보기

```bash
ezcut preview [디렉토리] [옵션]
```

분할된 타일을 이어붙여 원래 애니메이션처럼 미리볼 수 있는 창을 엽니다.

### 옵션

| 옵션 | 설명 |
| --- | --- |
| `--last` | 가장 최근 split 결과를 미리보기 |

### 예시

```bash
# 디렉토리 직접 지정
ezcut preview ./output_pieces

# 최근 결과 바로 미리보기
ezcut preview --last
```

### 키보드 조작

| 키 | 동작 |
| --- | --- |
| `Space` | 재생 / 일시정지 |
| `R` | 처음부터 다시 재생 |
| `Esc` / `Q` | 창 닫기 |

## `ezcut upload` - Mattermost 업로드

```bash
ezcut upload [디렉토리] [옵션]
```

분할된 타일을 Mattermost 커스텀 이모지로 일괄 업로드합니다.

현재 CLI 기준 업로드는 `manual` 로그인 흐름으로 동작합니다. 브라우저가 열리면 직접 로그인한 뒤 터미널에서 Enter를 눌러 진행하면 됩니다.

### 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--last` | 가장 최근 split 결과를 업로드 |  |
| `--limit`, `-l` | 업로드할 파일 수 제한 | 전체 |
| `--start-index` | 시작 인덱스 (1부터) | `1` |
| `--pause` | 업로드 간 대기 시간 (초) | `0.3` |
| `--headless` | 헤드리스 모드 (브라우저 창 숨김) | `false` |
| `--base-url` | Mattermost 서버 URL | 설정값 |
| `--add-path` | 이모지 추가 페이지 경로 | 설정값 |
| `--name-prefix` | 이모지 이름 접두어 | `""` |

### 예시

```bash
# 최근 결과 업로드
ezcut upload --last

# 1개만 테스트 업로드
ezcut upload ./output_pieces --limit 1

# 3번째 파일부터 업로드 재개
ezcut upload ./output_pieces --start-index 3
```

인자를 생략하면 터미널 화면 자체에서 **최근 히스토리를 목록 형태로 불러와 쌍방향으로 선택**할 수 있도록 유연한 가이드를 제공합니다.

## `ezcut share` - 갤러리 공유

```bash
ezcut share [디렉토리] [옵션]
```

생성된 커스텀 이모지 결과물을 중앙 [Ezcut Gallery](https://github.com/S-P-A-N/ezcut-gallery)에 투고합니다.

### 옵션

| 옵션 | 설명 |
| --- | --- |
| `--last` | 가장 최근 split 결과를 공유 |
| `--headless` | 브라우저 창을 띄우지 않고 공유 진행 |

`upload`와 마찬가지로 대상을 생략하면 이전 작업 내역(히스토리)에서 원하는 대상을 대화형 프롬프트로 찾아 고를 수 있게 안내가 나옵니다.

## `ezcut history` - 작업 히스토리

```bash
ezcut history [옵션]
```

이전 split 작업 기록과 함께 **Mattermost 업로드 여부**, **갤러리 공유 여부** 상태를 조회합니다.

### 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `-n`, `--limit` | 표시할 항목 수 | `10` |
| `--latest` | 최신 1건만 상세 표시 |  |

### 예시

```bash
# 최근 작업 목록
ezcut history

# 최근 5건만
ezcut history -n 5

# 최신 1건 상세 정보
ezcut history --latest
```

## 전체 워크플로 예시

```bash
# 1) GIF를 16x9로 분할
ezcut split ./nyancat.gif --cols 16 --rows 9 --name nyancat

# 2) 결과 확인
ezcut preview --last

# 3) 1개만 테스트 업로드
ezcut upload --last --limit 1

# 4) 일괄 업로드 진행
ezcut upload --last

# 5) 갤러리 공유
ezcut share --last
```

## 경로 및 명령 점검 메모

현재 문서의 예시는 모두 아래 기준으로 정리했습니다.

- 레거시 스크립트 경로(`./ezcut.py`, `./preview_gif_tiles.py`, `./mattermost_upload.py`)는 사용하지 않음
- 현재 패키지 엔트리포인트인 `ezcut` 서브커맨드 기준으로만 문서화
- 소스 저장소에서 실행할 때는 `uv run ezcut ...` 형식 사용
- 설치 후 실행할 때는 `ezcut ...` 형식 사용

즉, 이 문서의 명령은 현재 저장소 구조 기준으로 경로 오류 없이 사용 가능한 형태를 기준으로 작성했습니다.
