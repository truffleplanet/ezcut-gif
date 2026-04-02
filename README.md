# ezcut

애니메이션 GIF를 N×M 그리드 타일로 분할하고, 미리보기하고, Mattermost 커스텀 이모지로 업로드하며, [Ezcut Gallery](https://github.com/S-P-A-N/ezcut-gallery)에 손쉽게 공유할 수 있는 도구입니다.

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) 또는 pip
- Google Chrome
  - 업로드 기능에 필요합니다.

## 문서

- GUI 가이드: [gui.md](gui.md)
- CLI 가이드: [cli.md](cli.md)

## 설치

```bash
# uv로 설치 (권장)
uv tool install git+https://github.com/S-P-A-N/ezcut-gif.git

# 또는 pipx로 설치
pipx install git+https://github.com/S-P-A-N/ezcut-gif.git

# 또는 pip로 설치
pip install git+https://github.com/S-P-A-N/ezcut-gif.git
```

설치 후 아래 두 명령어를 사용할 수 있습니다.

- `ezcut`: CLI
- `ezcut-gui`: GUI

소스 저장소를 직접 실행하는 경우에는 프로젝트 루트에서 아래처럼 사용할 수 있습니다.

```bash
uv sync
uv run ezcut --help
uv run ezcut-gui
```

## 빠른 시작
인터랙티브 모드로 실행(권장)
- `ezcut`: CLI
- `ezcut-gui`: GUI

인터랙티브 없이 사용하는 것도 가능합니다. 아래는 예시입니다.
```bash
# 예시 
# 1) GIF를 그리드로 분할
ezcut split ./input.gif

# 2) 분할 결과 미리보기
ezcut preview --last

# 3) Mattermost에 이모지 업로드
ezcut upload --last
```

# 4) 이모지를 갤러리에 공유
ezcut share --last
```

`--last` 옵션은 가장 최근 split 결과를 자동으로 참조하며, 대상 경로가 주어지지 않을 경우 대화형(Interactive)으로 인터페이스가 표시되어 이전 히스토리 내역 중 하나를 간편하게 골라서 작업을 이어나갈 수 있습니다.

## 기여하기

개발 환경 설정, 코드 스타일, PR 가이드라인은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE)
