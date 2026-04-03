# Changelog

## [0.4.0](https://github.com/S-P-A-N/ezcut-gif/compare/v0.3.0...v0.4.0) (2026-04-03)


### Features

* GUI 업로드 완료 후 share 안내와 진행 상태 접근성 개선 ([9d7feb3](https://github.com/S-P-A-N/ezcut-gif/commit/9d7feb3364a8f88fdf048d5b4e07bd4728872c81))
* History 탭에서 emoji.txt 복사 버튼 추가 ([7f6b3b8](https://github.com/S-P-A-N/ezcut-gif/commit/7f6b3b89b9dd1abf72cd1e70e138378f6a69aef0))


### Bug Fixes

* Split 탭에 세로 스크롤을 추가해 작은 화면 접근성을 개선 ([25ab402](https://github.com/S-P-A-N/ezcut-gif/commit/25ab4024d7cf0139955abd19de4e08152cc87866))
* Upload/Share progress 영역이 화면 밖으로 벗어나지 않도록 수정 ([36590cf](https://github.com/S-P-A-N/ezcut-gif/commit/36590cf67203bb6ca69db4c692027580fca2fd84))

## [0.3.0](https://github.com/S-P-A-N/ezcut-gif/compare/v0.2.0...v0.3.0) (2026-04-03)


### Features

* CLI/GUI 환경에 업로드 및 갤러리 공유 인터페이스 추가 ([ebba495](https://github.com/S-P-A-N/ezcut-gif/commit/ebba495b1c5ba4a193faa49fa27acb822bb975b1))
* emoji 텍스트 유틸 추가 ([5850bd1](https://github.com/S-P-A-N/ezcut-gif/commit/5850bd1f7d0648a2bc8ac84f55cb8deeb814c16d))
* gif cut 유틸화 ([dcc4e2e](https://github.com/S-P-A-N/ezcut-gif/commit/dcc4e2ec34ab313a6f231ce77f188b1468ab56e2))
* GUI용 작업 상태 모델 추가 ([aaff337](https://github.com/S-P-A-N/ezcut-gif/commit/aaff3375f15196a47cc09c1ff92115dd9c6b8304))
* keyring 기반 자격 증명 저장소 정리 ([f60e1a9](https://github.com/S-P-A-N/ezcut-gif/commit/f60e1a952fa79cfa2c6b6648ad3d288ce9e4a474))
* legacy -&gt; splitter service로 이전 ([a9619dd](https://github.com/S-P-A-N/ezcut-gif/commit/a9619dd826d60a1af502c689776a52c9374d7290))
* manual 업로드 로그인 확인 팝업 추가 ([7dad460](https://github.com/S-P-A-N/ezcut-gif/commit/7dad460b968d8fea083c5579d254ea270116d5f1))
* mattermost 이메일 설정 추가 ([bff23cf](https://github.com/S-P-A-N/ezcut-gif/commit/bff23cf2e28ca7bd630e65a8b3b1a7c4490cd227))
* Mattermost 이모지 자동 업로드 및 공유 서비스 로직 구현 ([ac384f9](https://github.com/S-P-A-N/ezcut-gif/commit/ac384f93654d85ea3fd1170ad5530fea26cedb9b))
* mattermost 자동 로그인 구현 ([8e1a1a2](https://github.com/S-P-A-N/ezcut-gif/commit/8e1a1a26eb97a977146468180926d3f14b66260f))
* preview 동작방식 개선 ([305ac2f](https://github.com/S-P-A-N/ezcut-gif/commit/305ac2f9cc14c5542c53cad002b2b007c861c3d8))
* preview 타일 로딩 및 초기 상태 구현 ([ea61b1b](https://github.com/S-P-A-N/ezcut-gif/commit/ea61b1bfd0abfcdd103e459bc2eb1f480d3e4ce1))
* preview 타일 진행 및 리셋 로직 구현 ([3e343a4](https://github.com/S-P-A-N/ezcut-gif/commit/3e343a40ac3166307e17a78ae7e9a757ea171c6b))
* previewer 서비스 생성 ([77134fa](https://github.com/S-P-A-N/ezcut-gif/commit/77134fa1109eddde39d376ee94a701e7cbf6e106))
* repository config 추가 ([6e7353d](https://github.com/S-P-A-N/ezcut-gif/commit/6e7353da32d908edef35c3e68de3312812d6b631))
* repository credentials 추가 ([031896e](https://github.com/S-P-A-N/ezcut-gif/commit/031896e50ba26b489e24f14bb69b88cd90410df6))
* repository history 추가 ([6767001](https://github.com/S-P-A-N/ezcut-gif/commit/6767001aa2db25669681fe3101fcf3a7a6d1f32f))
* split, preview, upload GUI 탭 구현 ([787a55e](https://github.com/S-P-A-N/ezcut-gif/commit/787a55e473a502b6725cc10e4c7322e96c887501))
* Store 계층 구현 ([52f7b89](https://github.com/S-P-A-N/ezcut-gif/commit/52f7b899f3e4b6ceecaffc323355960e896077ed))
* Typer CLI 기반 골격 및 커맨드 구현 ([1108708](https://github.com/S-P-A-N/ezcut-gif/commit/110870823b3d6e4d9152d90dbebd4ca78ab48cb4))
* upload 실패 인덱스에 업로드 순번 표시 추가 ([0981b83](https://github.com/S-P-A-N/ezcut-gif/commit/0981b83fe5db59e94856523e7f297479fdcbcd56))
* upload 자동 로그인 연동 ([0308162](https://github.com/S-P-A-N/ezcut-gif/commit/0308162cec05e8558215c5234d9891f4cd2493c5))
* upload 탭 계정 저장 UI 추가 ([03c9582](https://github.com/S-P-A-N/ezcut-gif/commit/03c9582035f346f0c991a9adf7fc6bd735b547c7))
* uploader 서비스 생성 ([fd24041](https://github.com/S-P-A-N/ezcut-gif/commit/fd24041859914fc8ebc9272fd6e35b3c66b57376))
* 네이밍 유틸 추가 ([4f6d05f](https://github.com/S-P-A-N/ezcut-gif/commit/4f6d05fbe486bc891fc2cf51de48e880b69339b8))
* 대화형 히스토리 선택 도구 및 GUI 전용 History 탭 신설 ([c382a89](https://github.com/S-P-A-N/ezcut-gif/commit/c382a898a854546e1ae1111ad57a16ef8432ec64))
* 배속 기능 추가 ([633cf64](https://github.com/S-P-A-N/ezcut-gif/commit/633cf643d780f8295bdc9b5eb012ac9a48d7560d))
* 배포 설정 ([1e76be1](https://github.com/S-P-A-N/ezcut-gif/commit/1e76be1501f8ac12f0f7888588d7efb920f9a7c7))
* 버전 체크 캐싱 추가, 버전 비교 방식 변경 ([c8e6c8d](https://github.com/S-P-A-N/ezcut-gif/commit/c8e6c8d9fada387e7f024b763a4d8a5674ccb4e4))
* 버전관리 방식 변경 ([c9340a7](https://github.com/S-P-A-N/ezcut-gif/commit/c9340a783b9e7c044f2a5a504039e6c90bb529d6))
* 업데이트 기능 추가 ([12703b5](https://github.com/S-P-A-N/ezcut-gif/commit/12703b5f9e15f35c2cc6ce0f8925481156c07973))
* 업로드 대상 로딩 및 드라이버 초기화 구현 ([2e4dd84](https://github.com/S-P-A-N/ezcut-gif/commit/2e4dd845b39f7b2572f445fcf52d17d9e12f4e91))
* 업로드 실행 및 결과 집계 구현, store에 변수 추가 ([ce080ef](https://github.com/S-P-A-N/ezcut-gif/commit/ce080ef41c006eb91ad02fd6368b88d869d342b7))
* 용량 제어 인자 추가 ([2a11c43](https://github.com/S-P-A-N/ezcut-gif/commit/2a11c43370107f2bcdc8f440c54f5b95b90d0d7d))
* 용량 조절 로직 수정 ([f5e699b](https://github.com/S-P-A-N/ezcut-gif/commit/f5e699b5fd53c5dcfeb8c983adbc8451cf3bd705))


### Bug Fixes

* CodeRabbit 리뷰 반영 및 업로드 fallback 처리 보완 ([0f78f34](https://github.com/S-P-A-N/ezcut-gif/commit/0f78f3457fb145391320867a40e42f0eb155b3ac))
* GUI에서 갤러리 공유 완료 알림을 표시하도록 수정 ([7dae729](https://github.com/S-P-A-N/ezcut-gif/commit/7dae72942389e237562d3333e3ed75a6e53e1737))
* Lint 규칙에 맞게 코드 수정 ([34639cf](https://github.com/S-P-A-N/ezcut-gif/commit/34639cf7c65eda333441105c3ed3107e07ef55ab))
* linter에서 줄 길이를 체크하지 않도록 수정 ([339e14e](https://github.com/S-P-A-N/ezcut-gif/commit/339e14e95cdd4c8b80d8782406d9cb1e7bf6393b))
* linting ([2491c08](https://github.com/S-P-A-N/ezcut-gif/commit/2491c08b2be49616d4a56b8354197cb7de28dfe9))
* manual 업로드 로그인 팝업 즉시 표시 ([246d834](https://github.com/S-P-A-N/ezcut-gif/commit/246d834af274d61eb40bd17f89161e1a034535fe))
* mattermost 자동 로그인 페이지 전환 흐름 수정 ([f82c161](https://github.com/S-P-A-N/ezcut-gif/commit/f82c161e313060bcf5d3ac6ebe73aade45307483))
* max_pieces 상수 최대값 변경, store layer로 책임 분리 ([2e9c135](https://github.com/S-P-A-N/ezcut-gif/commit/2e9c135408dc6572b01b3bb1f5bef9a856d794f5))
* offer_gallery_share()가 가장 최근 작업만 참조하던 문제 해결 ([e0a70ec](https://github.com/S-P-A-N/ezcut-gif/commit/e0a70ec937bdda64e6b00eb96231fee61b8e06e2))
* preview 기능 문제 해결 ([ebd91fe](https://github.com/S-P-A-N/ezcut-gif/commit/ebd91fe789e70b99a661d1f904986e487a882f8d))
* preview 및 upload 설정 모델 정리, init에 previewer 추가 ([80c5a08](https://github.com/S-P-A-N/ezcut-gif/commit/80c5a0810c0f676c5c6cd123b3582272fee81953))
* share 시 작성자 이름을 묻고 업로드 직후 공유 상태를 갱신하도록 수정 ([82120d0](https://github.com/S-P-A-N/ezcut-gif/commit/82120d01bfd9cbafb1cf08ac30132c37bec29ae8))
* splitter에 emoji 텍스트 생성 로직 추가 ([f10842b](https://github.com/S-P-A-N/ezcut-gif/commit/f10842b690c09d4f7d3b0a3c19f2b45c4c8b7f4f))
* upload 추적 방식 개선 ([da2a2b9](https://github.com/S-P-A-N/ezcut-gif/commit/da2a2b9b270bfdafbd8bf05d99433f37c98d9c15))
* 로컬 개발 시 버전 표기 변경 ([59d5bfa](https://github.com/S-P-A-N/ezcut-gif/commit/59d5bfa05f69113e45b2de5805cd5a42f70e005c))
* 배속 범위와 최소 duration 제한 조정 ([f8d2683](https://github.com/S-P-A-N/ezcut-gif/commit/f8d2683bd07369784d46e9a20bec113503133f8d))
* 업로드 완료 이력이 있는 항목은 GUI 공유 버튼이 활성화되도록 수정 ([717891d](https://github.com/S-P-A-N/ezcut-gif/commit/717891db6da840ead0383bf62ac1b6b24553dfc4))


### Hot Fixes

* uv lock 최신화 ([176634c](https://github.com/S-P-A-N/ezcut-gif/commit/176634c4f82f90167983c0699096e1f94f3416ad))


### Documentation

* CONTRIBUTING.md 추가 ([a6ecc14](https://github.com/S-P-A-N/ezcut-gif/commit/a6ecc1461bab6666a7bc03cd7e3893ea501d6699))
* readme minor fix ([bbb3e39](https://github.com/S-P-A-N/ezcut-gif/commit/bbb3e39afd5a8afbe9864c46457b97b08ebdf526))
* test용 gif 추가 ([18a76d3](https://github.com/S-P-A-N/ezcut-gif/commit/18a76d364a30d8bf2cf98e8ba4678f2fd2d0cff8))
* 버전 업데이트(0.2.0) 및 사용 가이드라인 최신화 ([1c1f987](https://github.com/S-P-A-N/ezcut-gif/commit/1c1f98792d5f410cb54bd7029f9c06829d82cec4))
* 버전관리 문서화 ([ca50a43](https://github.com/S-P-A-N/ezcut-gif/commit/ca50a437fdfe578df89d5329a3e10f902e83a35a))
* 유저용 README 추가 ([1aa68a6](https://github.com/S-P-A-N/ezcut-gif/commit/1aa68a630427f0931aee3c082282822e262c7c58))
* 유저용 README 추가 ([525bdc1](https://github.com/S-P-A-N/ezcut-gif/commit/525bdc1a73b5c37417ce92d9c87e4714fec116fc))


### Chores

* CONTRIBUTING.md 갱신 ([be3e003](https://github.com/S-P-A-N/ezcut-gif/commit/be3e003751e31ed26c7a5083d8a1190a5e9e35a4))
* docstring 추가 ([98adf83](https://github.com/S-P-A-N/ezcut-gif/commit/98adf83a99626ee22bf95c050224e107b9064c00))
* Issue 템플릿 정의 ([4a228c0](https://github.com/S-P-A-N/ezcut-gif/commit/4a228c01034870afba90d1c6f094871bddaec498))
* keyring 의존성 추가 ([52ae164](https://github.com/S-P-A-N/ezcut-gif/commit/52ae16402c587152b570152b6184ca33c275d719))
* legacy 제거 ([1675127](https://github.com/S-P-A-N/ezcut-gif/commit/1675127c5e833e07d41ed6c6f2f7d985746deb80))
* PR Template 정의 ([86e70ab](https://github.com/S-P-A-N/ezcut-gif/commit/86e70abd9265b69186fde05bffcaba875b35ca74))
* README 변수표기 갱신 ([7fa1e85](https://github.com/S-P-A-N/ezcut-gif/commit/7fa1e85f8a6155c4b56be6de1120fc1cabed9a08))
* README 최신화 ([d217544](https://github.com/S-P-A-N/ezcut-gif/commit/d21754433016e1cce8f40e667cc0f3b696cab6fb))
* README에 uv 설치 과정 추가 ([2f70451](https://github.com/S-P-A-N/ezcut-gif/commit/2f704513819df28d6c61b0615485d96016d13f6c))
* ruff pre-commit, CI 설정 추가 ([a19d464](https://github.com/S-P-A-N/ezcut-gif/commit/a19d464ab66a36af89075cca3cc1b75f0406b0b0))
* uv 의존성 추가, README 최신화 ([ac9f26d](https://github.com/S-P-A-N/ezcut-gif/commit/ac9f26dac7656ded23ffe7625ad74ca8c04ec14c))
* 기존 코드 formatting, lint 교정 ([da707c8](https://github.com/S-P-A-N/ezcut-gif/commit/da707c88039870b6a45472e2dd8424cd8755da7d))
* 문서 변경 등등 ([3b51968](https://github.com/S-P-A-N/ezcut-gif/commit/3b519689c26b3de927d53adb2fc33b43ad254a9a))
* 버전 관리를 위한 의존성 추가 ([430fbad](https://github.com/S-P-A-N/ezcut-gif/commit/430fbad7a12820a4028ed5cd99786668490fb160))
* 자동화 기능을 위한 외부 의존성(selenium 등) 추가 ([763750b](https://github.com/S-P-A-N/ezcut-gif/commit/763750b51181d95844096a45c689552f236db30b))
* 패키지 엔트리포인트 구성 ([6abb5a5](https://github.com/S-P-A-N/ezcut-gif/commit/6abb5a55d138b9c4c9561eae9e3803c1667ed174))
* 프로젝스 설정 ([e9709e1](https://github.com/S-P-A-N/ezcut-gif/commit/e9709e1e0425dc659f33131f9ada2dfad96bf3b0))
* 프로젝트 뼈대 생성 ([4a0f0d1](https://github.com/S-P-A-N/ezcut-gif/commit/4a0f0d1351028f602289973bff57092f8e6a9983))
* 프로젝트 설정(CLAUDE.md, pre-commit) 업데이트 ([4d15a2a](https://github.com/S-P-A-N/ezcut-gif/commit/4d15a2afc64fbfd85d4314112865092722dde7e1))


### Refactoring

* History 탭에서 같은 이름의 최신 항목만 표시하도록 정리 ([9432257](https://github.com/S-P-A-N/ezcut-gif/commit/9432257546d0667190c3aa55b64e66c1fe0e1cc8))
* recommend_grid를 GUI에서 utils/grid.py로 추출 ([2af086c](https://github.com/S-P-A-N/ezcut-gif/commit/2af086cfdcbbb5e900abaae48877407531f3135f))
* uploader 로그인 흐름 분리 ([7718a0e](https://github.com/S-P-A-N/ezcut-gif/commit/7718a0e74d76fdb7f8e74dfca244f00d7e607ed6))
* 리포지토리 계층 간소화 및 상태/상수 구조 개선 ([1bb2eff](https://github.com/S-P-A-N/ezcut-gif/commit/1bb2efff8ccbf575d6c3fba838a7f47d36203734))
* 이모지 목록에서 추가 버튼으로 업로드 폼 재진입 방식 개선 ([464bf75](https://github.com/S-P-A-N/ezcut-gif/commit/464bf75d6197c5b4c54a316683b5768204b33cd4))
