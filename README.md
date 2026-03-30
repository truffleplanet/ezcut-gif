# ezcut

GIF 파일을 그리드로 분할하여 각 조각을 개별 GIF로 저장하는 CLI 도구.

## 설치

```bash
pip install -e .
```

## 사용법

```bash
# 기본 사용 (GCD 기반 자동 그리드, 128x128 조각)
ezcut input.gif

# 조각 크기 변경
ezcut input.gif -s 64

# 출력 디렉토리 지정
ezcut input.gif -o output/

# 그리드 수동 지정
ezcut input.gif --cols 4 --rows 3

# 직접 실행
python ezcut.py input.gif -s 256
```

## 동작 방식

1. 입력 GIF의 가로/세로 최대공약수(GCD)를 기반으로 그리드를 자동 계산합니다.
   - 예: 1920x1080 → GCD=120 → 16열 x 9행
2. 각 그리드 위치에서 프레임을 크롭합니다.
3. 각 조각을 지정 크기(기본 128x128)로 리사이즈합니다.
4. 애니메이션 GIF의 경우 각 조각도 애니메이션을 유지합니다.

## 출력

`{입력파일명}_pieces/` 디렉토리에 저장됩니다:

```text
input_pieces/
  row0_col00.gif
  row0_col01.gif
  ...
  row8_col15.gif
```
