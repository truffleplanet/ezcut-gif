# ezcut

애니메이션 GIF를 N×M 그리드 타일로 분할하고, 미리보기하고, Mattermost 커스텀 이모지로 업로드하며, [Ezcut Gallery](https://github.com/S-P-A-N/ezcut-gallery)에 손쉽게 공유할 수 있는 도구입니다.

## 📖 문서

- [GUI 사용 가이드](gui.md)
- [CLI 상세 가이드](cli.md)

## 요구 사항

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (권장) 또는 [pipx](https://github.com/pypa/pipx) / [pip](https://pip.pypa.io/en/stable/installation/)
- Google Chrome (업로드 기능에 필요)

## 설치 및 설정 (Installation)

사용 환경에 따라 아래 토글을 펼쳐 설치 과정을 진행해 주세요. `uv` 도구 설치 후 `PATH` 설정이 필수적입니다.

<details>
<summary>Windows (winget, PowerShell)</summary>

1. **uv 설치**: PowerShell에서 아래 명령어를 실행합니다.
   ```powershell
   winget install --id=astral-sh.uv -e
   ```
2. **PATH 설정**: uv로 설치한 도구들을 어디서든 실행할 수 있도록 경로를 등록합니다.
   ```powershell
   uv tool update-shell
   ```
3. **터미널 재시작**: 설정이 반영되도록 PowerShell 창을 닫고 다시 엽니다.
4. **앱 설치**: 아래 명령어로 `ezcut`을 설치합니다.
   ```powershell
   uv tool install git+https://github.com/S-P-A-N/ezcut-gif.git
   ```
</details>

<details>
<summary>macOS (Homebrew + zsh/bash)</summary>

1. **uv 설치**: 터미널에서 아래 명령어를 실행합니다.
   ```bash
   brew install uv
   ```
2. **PATH 설정**: uv로 설치한 도구들을 어디서든 실행할 수 있도록 경로를 등록합니다.
   ```bash
   uv tool update-shell
   ```
3. **환경 변수 반영**: 터미널을 재시작하거나 아래 명령어를 실행합니다.
   ```bash
   source ~/.zshrc  # 또는 사용 중인 쉘의 설정 파일 (~/.bashrc 등)
   ```
4. **앱 설치**: 아래 명령어로 `ezcut`을 설치합니다.
   ```bash
   uv tool install git+https://github.com/S-P-A-N/ezcut-gif.git
   ```
</details>

### 설치 완료 확인
설치가 완료되면 아래 두 명령어를 바로 사용할 수 있습니다.

- `ezcut`: CLI 실행
- `ezcut-gui`: GUI 실행

### 버전 및 업데이트 관리

설치 후 아래 명령어를 통해 버전을 확인하고 최신 상태로 유지할 수 있습니다.

- `ezcut --version`: 현재 설치된 버전 확인
- `ezcut update`: 최신 버전 확인 및 업데이트 방법 안내

> [!TIP]
> **GUI 알림**: `ezcut-gui` 실행 시 하단 상태바에 업데이트 알림이 표시됩니다. 클릭 시 업데이트 가이드를 볼 수 있습니다.

> [!IMPORTANT]
> 만약 `ezcut: command not found` 에러가 발생한다면, `uv tool update-shell` 실행 후 터미널을 완전히 종료했다가 다시 시작했는지 확인해 주세요.

### 기타 설치 방법 (Alternative Methods)

`uv`를 사용하지 않거나 기존 방식(`pip`, `pipx`)을 선호하는 경우 아래 명령어를 사용하세요.

```bash
# pipx로 설치 (권장)
pipx install git+https://github.com/S-P-A-N/ezcut-gif.git

# 또는 pip로 설치
pip install git+https://github.com/S-P-A-N/ezcut-gif.git
```


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

# 4) 이모지를 갤러리에 공유
ezcut share --last
```

`--last` 옵션은 가장 최근 split 결과를 자동으로 참조하며, 대상 경로가 주어지지 않을 경우 대화형(Interactive)으로 인터페이스가 표시되어 이전 히스토리 내역 중 하나를 간편하게 골라서 작업을 이어나갈 수 있습니다.

## 기여하기

개발 환경 설정, 코드 스타일, PR 가이드라인은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE)
