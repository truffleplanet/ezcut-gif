# ezcut

GIF를 여러 조각으로 잘라서 각 조각을 개별 GIF로 저장하고, 다시 이어붙여 미리보기하거나 Mattermost 커스텀 이모지로 업로드할 수 있는 도구 모음입니다.

이 문서의 모든 경로 예시는 저장소 루트를 기준으로 한 상대경로입니다.

## 구성

- `ezcut.py`: 원본 GIF를 타일 GIF들로 분할
- `preview_gif_tiles.py`: 분할된 타일들을 다시 이어붙여 미리보기
- `mattermost_upload.py`: Mattermost 커스텀 이모지 추가 페이지에 순서대로 업로드

## 요구 사항

- Python 3.9+
- Google Chrome

필요한 Python 패키지는 `pyproject.toml`로 관리됩니다.

## 설치

### PowerShell

```powershell
py -m pip install -e .
```

### Bash

```bash
python -m pip install -e .
```

## 1. GIF 분할

기본적으로 입력 GIF의 가로/세로 비율을 보고 그리드를 계산한 뒤, 각 조각을 정사각형 GIF로 저장합니다.

### PowerShell

```powershell
# 기본 사용
py .\ezcut.py .\input.gif

# 16x9로 강제 분할, 파일명 접두사 ai, 출력 폴더 지정
py .\ezcut.py .\ai.gif --cols 16 --rows 9 -n ai -o .\ai_pieces
```

### Bash

```bash
# 기본 사용
python ./ezcut.py ./input.gif

# 16x9로 강제 분할, 파일명 접두사 ai, 출력 폴더 지정
python ./ezcut.py ./ai.gif --cols 16 --rows 9 -n ai -o ./ai_pieces
```

지원 옵션:

- `-s`, `--size`: 출력 조각 크기. 기본값 `128`
- `-o`, `--output-dir`: 출력 디렉토리
- `--cols`: 열 수 수동 지정
- `--rows`: 행 수 수동 지정
- `-n`, `--name`: 출력 파일 접두사와 `emoji.txt`용 이름

예를 들어 `1920x1080` GIF를 `16 x 9`로 분할하면 다음과 같은 파일이 만들어집니다.

```text
ai_pieces/
  ai-a01.gif
  ai-a02.gif
  ai-a03.gif
  ...
  ai-i16.gif
  emoji.txt
```

파일명 규칙:

- 행: `a`, `b`, `c` ...
- 열: `01`, `02`, `03` ...
- 형식: `{name}-{row}{col}.gif`

## 2. 타일 미리보기

`preview_gif_tiles.py`는 출력 디렉토리의 `emoji.txt`를 읽어 타일 순서를 자동으로 파악한 뒤, 원래 애니메이션처럼 이어붙여 보여줍니다.

### PowerShell

```powershell
# 기본 미리보기
py .\preview_gif_tiles.py .\ai_pieces

# 반 크기로 미리보기
py .\preview_gif_tiles.py .\ai_pieces --scale 0.5
```

### Bash

```bash
# 기본 미리보기
python ./preview_gif_tiles.py ./ai_pieces

# 반 크기로 미리보기
python ./preview_gif_tiles.py ./ai_pieces --scale 0.5
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
py .\mattermost_upload.py .\ai_pieces --limit 1

# a02부터 끝까지 업로드
py .\mattermost_upload.py .\ai_pieces --start-index 2

# 로그인 세션을 재사용할 전용 크롬 프로필 사용
py .\mattermost_upload.py .\ai_pieces --start-index 2 --user-data-dir .\chrome-meeting-profile
```

### Bash

```bash
# 1개만 테스트
python ./mattermost_upload.py ./ai_pieces --limit 1

# a02부터 끝까지 업로드
python ./mattermost_upload.py ./ai_pieces --start-index 2

# 로그인 세션을 재사용할 전용 크롬 프로필 사용
python ./mattermost_upload.py ./ai_pieces --start-index 2 --user-data-dir ./chrome-meeting-profile
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
py .\ezcut.py .\ai.gif --cols 16 --rows 9 -n ai -o .\ai_pieces

# 2) 전체 화면 미리보기
py .\preview_gif_tiles.py .\ai_pieces --scale 0.5

# 3) 업로드 테스트 1개
py .\mattermost_upload.py .\ai_pieces --limit 1

# 4) a02부터 끝까지 업로드
py .\mattermost_upload.py .\ai_pieces --start-index 2 --user-data-dir .\chrome-meeting-profile
```

### Bash

```bash
# 1) 원본 GIF 분할
python ./ezcut.py ./ai.gif --cols 16 --rows 9 -n ai -o ./ai_pieces

# 2) 전체 화면 미리보기
python ./preview_gif_tiles.py ./ai_pieces --scale 0.5

# 3) 업로드 테스트 1개
python ./mattermost_upload.py ./ai_pieces --limit 1

# 4) a02부터 끝까지 업로드
python ./mattermost_upload.py ./ai_pieces --start-index 2 --user-data-dir ./chrome-meeting-profile
```
