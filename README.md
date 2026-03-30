# ezcut

GIF를 여러 조각으로 잘라서 각 조각을 개별 GIF로 저장하고, 다시 이어붙여 미리보기하거나 Mattermost 커스텀 이모지로 업로드할 수 있는 도구 모음입니다.

이 문서의 모든 경로 예시는 저장소 루트를 기준으로 한 상대경로입니다.

## 구성

- `ezcut.py`: 원본 GIF를 타일 GIF들로 분할
- `preview_gif_tiles.py`: 분할된 타일들을 다시 이어붙여 미리보기
- `mattermost_upload.py`: Mattermost 커스텀 이모지 추가 페이지에 순서대로 업로드

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Google Chrome

## 설치 및 개발 환경 설정

`uv`를 사용하여 의존성을 설치하고 개발 도구를 준비합니다.

```bash
# 의존성 설치 및 가상환경 구성
uv sync

# (선택) 로컬 git pre-commit 훅 등록
uv run pre-commit install
```

## 코드 스타일 및 린트 관리 (Ruff)

본 프로젝트는 [Ruff](https://docs.astral.sh/ruff/)를 사용하여 코드 스타일과 품질을 관리합니다. 커밋 시 자동으로 체크되지만, 수동으로 전체 프로젝트를 교정하고 싶을 때는 아래 명령어를 사용합니다.

```bash
# 코드 포맷팅 및 린트 자동 수정 (가장 권장하는 방법)
uv run pre-commit run --all-files

# 또는 개별 실행
uv run ruff format .      # 포맷팅만 수행
uv run ruff check --fix .   # 린트 오류 자동 수정 및 임포트 정렬
```

## 1. GIF 분할

기본적으로 입력 GIF의 가로/세로 비율을 보고 그리드를 계산한 뒤, 각 조각을 정사각형 GIF로 저장합니다.

### PowerShell

```powershell
# 기본 사용
uv run python .\ezcut.py .\{input}.gif

# 16x9로 강제 분할, 파일명 접두사 ai, 출력 폴더 지정
uv run python .\ezcut.py .\{input}.gif --cols 16 --rows 9 -n {output-prefix} -o .\{output-dir}
```

### Bash

```bash
# 기본 사용
uv run python ./ezcut.py ./{input}.gif

# 16x9로 강제 분할, 파일명 접두사 ai, 출력 폴더 지정
uv run python ./ezcut.py ./{input}.gif --cols 16 --rows 9 -n {output-prefix} -o ./{output-dir}
```

지원 옵션:

- `-s`, `--size`: 출력 조각 크기. 기본값 `128`
- `-o`, `--output-dir`: 출력 디렉토리
- `--cols`: 열 수 수동 지정
- `--rows`: 행 수 수동 지정
- `-n`, `--name`: 출력 파일 접두사와 `emoji.txt`용 이름

예를 들어 `1920x1080` GIF를 `16 x 9`로 분할하면 다음과 같은 파일이 만들어집니다.

```text
{output-dir}/
  {output-prefix}-a01.gif
  {output-prefix}-a02.gif
  {output-prefix}-a03.gif
  ...
  {output-prefix}-i16.gif
  emoji.txt
```

파일명 규칙:

- 행: `a`, `b`, `c` ...
- 열: `01`, `02`, `03` ...
- 형식: `{output-prefix}-{row}{col}.gif`

## 2. 타일 미리보기

`preview_gif_tiles.py`는 출력 디렉토리의 `emoji.txt`를 읽어 타일 순서를 자동으로 파악한 뒤, 원래 애니메이션처럼 이어붙여 보여줍니다.

### PowerShell

```powershell
# 기본 미리보기
uv run python .\preview_gif_tiles.py .\{output-dir}

# 반 크기로 미리보기
uv run python .\preview_gif_tiles.py .\{output-dir} --scale 0.5
```

### Bash

```bash
# 기본 미리보기
uv run python ./preview_gif_tiles.py ./{output-dir}

# 반 크기로 미리보기
uv run python ./preview_gif_tiles.py ./{output-dir} --scale 0.5
```

지원 옵션:

- `directory` (positional): GIF 타일이 있는 디렉토리. 기본값 `.` (현재 디렉토리)
- `--scale`: 표시 배율. 지정하지 않으면 화면 크기에 맞춰 자동 조절
- `--background`: 배경색. 기본값 `#000000`

조작:

- `space`: 일시정지/재생
- `r`: 처음부터 다시 재생
- `esc`: 창 닫기

## 3. Mattermost 업로드

`mattermost_upload.py`는 Mattermost 커스텀 이모지 추가 페이지에서 다음 순서로 동작합니다.

1. 파일명 순서대로 업로드 대상을 읽음
2. `input#name`에 이모지 이름 입력
3. `input#select-emoji`에 파일 경로 입력
4. `저장` 버튼 클릭
5. 다음 파일로 반복

처음 실행 시 브라우저가 열리면 직접 로그인한 뒤 터미널에서 Enter를 누르면 됩니다.

### PowerShell

```powershell
# 1개만 테스트
uv run python .\mattermost_upload.py .\{output-dir} --limit 1

# 로그인 세션을 재사용할 전용 크롬 프로필 사용
uv run python .\mattermost_upload.py .\{output-dir} --user-data-dir .\chrome-profile
```

### Bash

```bash
# 1개만 테스트
uv run python ./mattermost_upload.py ./{output-dir} --limit 1

# 로그인 세션을 재사용할 전용 크롬 프로필 사용
uv run python ./mattermost_upload.py ./{output-dir} --user-data-dir ./chrome-profile
```

지원 옵션:

- `directory` (positional): 업로드할 이미지 폴더
- `--start-index`: 몇 번째 파일부터 시작할지 지정
- `--limit`: 업로드 개수 제한
- `--pause`: 업로드 사이 대기 시간(초)
- `--add-path`: 이모지 추가 페이지 상대경로 또는 전체 URL
- `--user-data-dir`: 로그인 세션을 재사용할 크롬 프로필 폴더

## 예시 워크플로

### PowerShell

```powershell
# 1) 원본 GIF 분할
uv run python .\ezcut.py .\{input}.gif --cols 16 --rows 9 -n {output-prefix} -o .\{output-dir}

# 2) 전체 화면 미리보기
uv run python .\preview_gif_tiles.py .\{output-dir} --scale 0.5

# 3) 업로드
uv run python .\mattermost_upload.py .\{output-dir} --user-data-dir .\chrome-profile
```

### Bash

```bash
# 1) 원본 GIF 분할
uv run python ./ezcut.py ./{input}.gif --cols 16 --rows 9 -n {output-prefix} -o ./{output-dir}

# 2) 전체 화면 미리보기
uv run python ./preview_gif_tiles.py ./{output-dir} --scale 0.5

# 3) 업로드
uv run python ./mattermost_upload.py ./{output-dir} --user-data-dir ./chrome-profile
```
