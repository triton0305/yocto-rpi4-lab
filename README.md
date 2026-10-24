Yocto Raspberry Pi 4 Lab
Yocto Project로 Raspberry Pi 4B(ARM64)용 Embedded Linux 시스템을 구성하고, 실제 보드에서 검증하는 실습 저장소입니다.

**주 빌드 환경(Primary Build Host)**과 **로컬 개발 환경(Local Development Host)**에 개발 환경을 구성했습니다. 로컬 개발 환경에서는 bitbake -p를 통한 Recipe Parse 검증까지 통과했습니다(사용자 제공 실행 기록). Linux 이미지 빌드·실장비 부팅·Custom Layer 및 Recipe 통합은 아직 완료하지 않았습니다. 문서에는 완료한 작업과 후속 학습 목표를 구분하여 기록합니다.
목표
- BitBake, OpenEmbedded, Layer, Recipe의 역할과 의존성 이해
- Raspberry Pi 4B용 Linux 이미지 빌드와 산출물 분석
- Custom Layer와 Recipe 작성 및 C Application 통합
- Linux Kernel 및 Device Driver 통합
- Raspberry Pi 4B에서 부팅·동작 검증 및 문제 해결 기록
개발 환경
항목	구성
Host	WSL2 Ubuntu (x86-64)
Target	Raspberry Pi 4 Model B (ARM64 / AArch64)
Yocto Project	6.0.4 (wrynose)
DISTRO	poky
MACHINE	raspberrypi4-64
BSP Layer	meta-raspberrypi


Host별 빌드 자원과 병렬 설정은 다음과 같습니다.
항목	주 빌드 환경 (Primary Build Host)	로컬 개발 환경 (Local Development Host)
OS	WSL2 Ubuntu 22.04	WSL2 Ubuntu 26.04.1 LTS
논리 CPU	24	8
RAM	15GiB	7.6GiB
BB_NUMBER_THREADS	4	2
PARALLEL_MAKE	-j 4	-j 2


환경 구성 절차는 [Chapter 1](docs/01-environment.md)에, 실제 출력 증거는 [주 빌드 환경 로그](docs/logs/01-center-setup.md)와 [로컬 개발 환경 로그](docs/logs/01-home-setup.md)에, 설정값의 의미는 [빌드 설정](configs/build-config.md)에 기록합니다.
학습 진행 현황
- [x] Chapter 1 — Yocto 개발 환경 구성
- [ ] Chapter 2 — BitBake · Layer · Recipe 구조
- [ ] Chapter 3 — 최소 Linux 이미지 빌드
- [ ] Chapter 4 — RootFS 및 빌드 산출물 분석
- [ ] Chapter 5 — Raspberry Pi 4B 부팅 검증
- [ ] Chapter 6 — Custom Layer 제작
- [ ] Chapter 7 — Custom Recipe 및 C Application
- [ ] Chapter 8 — Kernel 및 Device Driver 통합
- [ ] Chapter 9 — 증분 빌드 · 의존성 · 오류 분석
체크한 항목은 기존 실습 기록을 기준으로 합니다. 로컬 개발 환경에서 bitbake -p를 실행해 .bb 992개, 2013 targets, 73 skipped, 0 errors, 종료 코드 0을 확인했습니다(사용자 제공 결과). 이는 메타데이터 Parse 검증이며 컴파일·이미지 빌드·실장비 부팅 검증은 아닙니다.
저장소 구조
yocto-rpi4-lab/
├── README.md
├── configs/
│   ├── build-config.md
│   └── source-revisions.md
└── docs/
    ├── 01-environment.md
    └── logs/
        ├── 01-center-setup.md
        └── 01-home-setup.md
위 구조는 본 문서 정비 후 GitHub main 브랜치에 게시된 것으로 기록된 파일을 표시합니다. scripts/, Custom Layer 및 Recipe 디렉터리는 필요할 때 생성하고 검증 후 추가할 예정입니다. 로그 파일명은 기존 GitHub 링크의 호환성을 위해 유지하되, 문서 안의 Host 명칭은 역할 기준으로 표기합니다.
기술 문서
문서	역할
[Chapter 1 — 개발 환경 구성](docs/01-environment.md)	수행한 명령·원리·환경 검증
[주 빌드 환경 — Chapter 1 실행 근거](docs/logs/01-center-setup.md)	주 빌드 환경의 오류 원문·검증 결과·미확인 항목
[로컬 개발 환경 — Chapter 1 실행 로그](docs/logs/01-home-setup.md)	로컬 개발 환경의 명령·실제 출력·Checkout SHA·Parse 결과
[빌드 설정](configs/build-config.md)	설정값·적용 위치·동작 원리·확인 명령
[소스 리비전](configs/source-revisions.md)	외부 저장소의 기록된 Commit SHA 및 재현성 점검


관리 원칙
- GitHub에는 직접 작성한 Source, Custom Layer, Recipe, 설정 설명과 검증 기록을 관리합니다.
- Yocto 원본 Source, 다운로드 파일, 빌드 캐시, 이미지 등의 대용량 생성물은 커밋하지 않습니다.
- 변경·문제 해결 기록에는 현상 → 원인 → 해결 → 검증을 남깁니다.
- 실행하지 않은 명령은 확인 절차로 구분하고, 검증하지 않은 값은 추정하여 채우지 않습니다.
- 주 빌드 환경과 로컬 개발 환경의 실제 Checkout Commit 및 Host 환경은 재현 전에 다시 대조합니다.
현재 상태
Chapter 1 개발 환경 구성 및 로컬 개발 환경의 BitBake Parse 검증을 완료했습니다(제공된 실습 결과 기준). 다음 단계는 Chapter 2의 BitBake · Layer · Recipe 분석이며, 이미지 빌드와 실장비 부팅은 아직 수행하지 않았습니다.
