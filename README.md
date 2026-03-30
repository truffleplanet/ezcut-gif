# ezcut

GIF를 여러 조각으로 잘라서 각 조각을 개별 GIF로 저장하는 CLI 도구입니다.

기본 목적은 큰 애니메이션을 채팅/이모지 업로드용 타일로 분해하고, 필요하면 다시 이어붙여 미리보기하는 것입니다.

## 요구 사항

- Python 3.9+
- Pillow

## 설치

프로젝트 폴더에서:

```bash
py -m pip install -e .
```

설치하지 않고 파일로 직접 실행해도 됩니다.

## 빠른 시작

### 1. GIF 분할

```bash
# 기본 사용: 비율 기준 자동 그리드 계산, 출력 크기 128x128
py .\ezcut.py input.gif

# 설치 후 엔트리포인트로 실행
ezcut input.gif
```

예를 들어 1920x1080 GIF는 자동으로 `16 x 9` 그리드가 잡히고, 각 조각은 기본적으로 `128x128`으로 저장됩니다.

### 2. 타일 미리보기

분할된 GIF들이 같은 폴더에 있으면:

```bash
py .\preview_gif_tiles.py
```

더 작게 띄우려면:

```bash
py .\preview_gif_tiles.py --scale 0.5
```

## `ezcut.py` 옵션

```bash
py .\ezcut.py input.gif -s 64
py .\ezcut.py input.gif -o output\
py .\ezcut.py input.gif --cols 16 --rows 9
py .\ezcut.py input.gif -n ai
```

지원 옵션:

- `-s`, `--size`: 출력 조각 크기. 기본값 `128`
- `-o`, `--output-dir`: 출력 디렉토리
- `--cols`: 열 수 수동 지정
- `--rows`: 행 수 수동 지정
- `-n`, `--name`: 출력 파일 접두사와 `emoji.txt`용 이름

## 동작 방식

1. 입력 GIF의 해상도를 읽습니다.
2. `--cols`, `--rows`가 없으면 가로/세로 최대공약수로 그리드를 계산합니다.
3. 각 프레임을 타일 단위로 잘라냅니다.
4. 각 조각을 지정된 정사각형 크기로 리사이즈합니다.
5. 각 조각을 개별 애니메이션 GIF로 저장합니다.
6. 업로드용 문자열 묶음인 `emoji.txt`도 함께 생성합니다.

## 출력 형식

기본 출력 디렉토리는 `{입력파일명}_pieces/` 입니다.

예:

```text
gaguya_pieces/
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
- 최종 형식: `{name}-{row}{col}.gif`

즉 `16 x 9` 그리드라면 `a01`부터 `i16`까지 생성됩니다.

## 용량 최적화

출력 GIF 하나가 512KB를 넘으면 프레임 스킵을 자동으로 적용합니다.

가장 큰 조각 기준으로 최적 스킵 단계를 찾은 뒤, 같은 전략으로 전체 타일을 저장합니다.

## `preview_gif_tiles.py`

분할된 GIF들을 다시 붙여서 전체 애니메이션을 눈으로 확인하는 로컬 미리보기 도구입니다.

출력 디렉토리의 `emoji.txt`를 읽어 그리드 구조와 파일 목록을 자동으로 파악합니다.

기본 예시:

```bash
py .\preview_gif_tiles.py gaguya_pieces/
```

지원 옵션:

- `directory` (positional): GIF 타일이 있는 디렉토리. 기본값 `.` (현재 디렉토리)
- `--scale`: 표시 배율. 지정하지 않으면 화면 크기에 맞춰 자동 조절
- `--background`: 배경색. 기본값 `#000000`

조작:

- `space`: 일시정지/재생
- `r`: 처음부터 다시 재생
- `esc`: 창 닫기

## 예시 워크플로

```bash
# 1) 원본 GIF 분할
py .\ezcut.py .\gaguya.gif --cols 16 --rows 9 -n ai

# 2) 이어붙인 전체 화면 미리보기
py .\preview_gif_tiles.py gaguya_pieces/
```
