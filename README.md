# ezcut

애니메이션 GIF를 N×M 그리드 타일로 분할하고, 미리보기하고, Mattermost 커스텀 이모지로 일괄 업로드하는 도구입니다.

<!-- TODO: 데모 GIF/스크린샷 추가 -->

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) 또는 pip
- Google Chrome (업로드 기능에 필요)

## 설치

```bash
# uv로 설치 (권장)
uv tool install git+https://github.com/S-P-A-N/ezcut-gif.git

# 또는 pipx로 설치
pipx install git+https://github.com/S-P-A-N/ezcut-gif.git

# 또는 pip로 설치
pip install git+https://github.com/S-P-A-N/ezcut-gif.git
```

설치 후 `ezcut` (CLI)과 `ezcut-gui` (GUI) 두 개의 명령어가 등록됩니다.

## 빠른 시작

```bash
# 1) GIF를 그리드로 분할
ezcut split ./input.gif

# 2) 분할 결과 미리보기
ezcut preview --last

# 3) Mattermost에 이모지 업로드
ezcut upload --last
```

`--last` 옵션은 가장 최근 split 결과를 자동으로 참조합니다.

## GUI 사용법

```bash
ezcut-gui
```

<!-- TODO: GUI 사용법 작성 예정 -->

---

## CLI 사용법

### 인터랙티브 모드

인자 없이 `ezcut`만 실행하면 화살표 키로 동작을 선택할 수 있는 인터랙티브 홈 메뉴가 표시됩니다.

```bash
ezcut
```

각 명령어도 필수 인자를 생략하면 위자드가 단계별로 안내합니다.

---

### `ezcut split` — GIF 분할

```bash
ezcut split <GIF 파일> [옵션]
```

GIF 파일을 N×M 그리드로 분할하여 각 조각을 개별 GIF로 저장합니다. 인자를 생략하면 위자드가 안내합니다.

| 옵션                 | 설명                    | 기본값                    |
| -------------------- | ----------------------- | ------------------------- |
| `--cols`, `-c`       | 가로 조각 수            | GIF 비율에 맞춰 자동 계산 |
| `--rows`, `-r`       | 세로 조각 수            | GIF 비율에 맞춰 자동 계산 |
| `--size`, `-s`       | 타일 크기 (px)          | `128`                     |
| `--max-size`         | 타일 최대 파일 크기 (KB)  | `512`                     |
| `--output-dir`, `-o` | 출력 디렉토리           | `{파일명}_pieces/`        |
| `--name`, `-n`       | 이모지 베이스 이름      | 파일명                    |
| `--speed`            | 배속 (1.0 = 원본)       | `1.0`                     |

```bash
# 16x9 그리드로 분할, 이모지 이름 지정
ezcut split ./input.gif --cols 16 --rows 9 --name my-emoji

# 타일 크기 64px, 최대 256KB 제한
ezcut split ./input.gif -s 64 --max-size 256
```

분할이 완료되면 출력 디렉토리에 타일 GIF와 `emoji.txt` 파일이 생성됩니다.

```text
output_pieces/
├── my-emoji-a01.gif
├── my-emoji-a02.gif
├── ...
├── my-emoji-i16.gif
└── emoji.txt          # 미리보기/업로드에서 그리드 구조 파악에 사용
```

타일 파일명 규칙: `{이름}-{행}{열}.gif` (행: `a`~`z`, 열: `01`, `02`, ...)

---

### `ezcut preview` — 미리보기

```bash
ezcut preview [디렉토리] [옵션]
```

분할된 타일을 이어붙여 원래 애니메이션처럼 미리볼 수 있는 창을 엽니다.

| 옵션     | 설명                             |
| -------- | -------------------------------- |
| `--last` | 가장 최근 split 결과를 미리보기  |

```bash
# 디렉토리 직접 지정
ezcut preview ./output_pieces

# 최근 결과 바로 미리보기
ezcut preview --last
```

**키보드 조작:**

| 키          | 동작               |
| ----------- | ------------------ |
| `Space`     | 재생 / 일시정지    |
| `R`         | 처음부터 다시 재생 |
| `Esc` / `Q` | 창 닫기            |

---

### `ezcut upload` — Mattermost 업로드

```bash
ezcut upload [디렉토리] [옵션]
```

분할된 타일을 Mattermost 커스텀 이모지로 일괄 업로드합니다. 처음 실행 시 브라우저가 열리면 직접 로그인한 뒤 터미널에서 Enter를 누르세요.

| 옵션              | 설명                           | 기본값   |
| ----------------- | ------------------------------ | -------- |
| `--last`          | 가장 최근 split 결과를 업로드  |          |
| `--limit`, `-l`   | 업로드할 파일 수 제한          | 전체     |
| `--start-index`   | 시작 인덱스 (1부터)            | `1`      |
| `--pause`         | 업로드 간 대기 시간 (초)       | `0.3`    |
| `--headless`      | 헤드리스 모드 (브라우저 창 숨김) | `false`  |
| `--base-url`      | Mattermost 서버 URL            | 설정값   |
| `--add-path`      | 이모지 추가 페이지 경로        | 설정값   |
| `--name-prefix`   | 이모지 이름 접두어             | `""`     |

```bash
# 최근 결과 업로드
ezcut upload --last

# 1개만 테스트 업로드
ezcut upload ./output_pieces --limit 1

# 3번째 파일부터 업로드 재개
ezcut upload ./output_pieces --start-index 3
```

---

### `ezcut history` — 작업 히스토리

```bash
ezcut history [옵션]
```

이전 split 작업 기록을 조회합니다.

| 옵션            | 설명                | 기본값 |
| --------------- | ------------------- | ------ |
| `-n`, `--limit` | 표시할 항목 수      | `10`   |
| `--latest`      | 최신 1건만 상세 표시 |        |

```bash
# 최근 작업 목록
ezcut history

# 최근 5건만
ezcut history -n 5

# 최신 1건 상세 정보
ezcut history --latest
```

---

## 전체 워크플로 예시

```bash
# 1) GIF를 16x9로 분할
ezcut split ./nyancat.gif --cols 16 --rows 9 --name nyancat

# 2) 결과 확인
ezcut preview --last

# 3) 1개만 테스트 업로드
ezcut upload --last --limit 1

# 4) 전체 업로드
ezcut upload --last
```

---

## 기여하기

개발 환경 설정, 코드 스타일, PR 가이드라인은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE)
