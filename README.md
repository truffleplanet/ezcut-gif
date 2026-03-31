# ezcut

애니메이션 GIF를 N×M 그리드 타일로 분할하고, 미리보기하고, Mattermost 커스텀 이모지로 업로드하는 도구입니다.

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

```bash
# 1) GIF를 그리드로 분할
ezcut split ./input.gif

# 2) 분할 결과 미리보기
ezcut preview --last

# 3) Mattermost에 이모지 업로드
ezcut upload --last
```

`--last` 옵션은 가장 최근 split 결과를 자동으로 참조합니다.

## 기여하기

개발 환경 설정, 코드 스타일, PR 가이드라인은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE)
