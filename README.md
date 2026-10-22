# Yocto Raspberry Pi 4 Lab

Yocto Project로 Raspberry Pi 4B(ARM64)용 Embedded Linux 시스템을 구성하고, 실제 보드에서 검증하는 실습 저장소입니다.

현재는 개발 환경을 구성한 단계이며, Linux 이미지 빌드·실장비 부팅·Custom Layer 및 Recipe 통합은 완료하지 않았습니다. 문서에는 **완료한 작업**과 **후속 학습 목표**를 구분하여 기록합니다.

## 목표

- BitBake, OpenEmbedded, Layer, Recipe의 역할과 의존성 이해
- Raspberry Pi 4B용 Linux 이미지 빌드와 산출물 분석
- Custom Layer와 Recipe 작성 및 C Application 통합
- Linux Kernel 및 Device Driver 통합
- Raspberry Pi 4B에서 부팅·동작 검증 및 문제 해결 기록

## 개발 환경

| 항목 | 현재 기록 |
|---|---|
| Host | WSL2 Ubuntu (x86-64) |
| Target | Raspberry Pi 4 Model B (ARM64 / AArch64) |
| Yocto Project | 6.0.4 (wrynose) |
| DISTRO | `poky` |
| MACHINE | `raspberrypi4-64` |
| BSP Layer | `meta-raspberrypi` |

환경 구성 절차와 실제 확인 결과는 [Chapter 1](docs/01-environment.md)에, 설정의 출처와 변수 의미는 [빌드 설정](configs/build-config.md)에 기록합니다.

## 학습 진행 현황

- [x] Chapter 1 — Yocto 개발 환경 구성
- [ ] Chapter 2 — BitBake · Layer · Recipe 구조
- [ ] Chapter 3 — 최소 Linux 이미지 빌드
- [ ] Chapter 4 — RootFS 및 빌드 산출물 분석
- [ ] Chapter 5 — Raspberry Pi 4B 부팅 검증
- [ ] Chapter 6 — Custom Layer 제작
- [ ] Chapter 7 — Custom Recipe 및 C Application
- [ ] Chapter 8 — Kernel 및 Device Driver 통합
- [ ] Chapter 9 — 증분 빌드 · 의존성 · 오류 분석

체크한 항목은 기존 실습 기록을 기준으로 합니다. 현재 `core-image-minimal` 빌드와 Raspberry Pi 부팅 검증은 **미진행**입니다.

## 저장소 구조

```text
yocto-rpi4-lab/
├── README.md
├── configs/
│   ├── build-config.md
│   └── source-revisions.md
└── docs/
    └── 01-environment.md
```

위 구조는 2026-10-22 기준 GitHub `main` 브랜치에 실제 존재하는 파일만 표시한 것입니다. `scripts/`, Custom Layer 및 Recipe 디렉터리는 필요할 때 생성하고 검증 후 추가할 예정입니다.

## 기술 문서

| 문서 | 역할 |
|---|---|
| [Chapter 1 — 개발 환경 구성](docs/01-environment.md) | 수행한 명령·오류 해결·환경 검증 |
| [빌드 설정](configs/build-config.md) | 설정값·적용 위치·동작 원리·확인 명령 |
| [소스 리비전](configs/source-revisions.md) | 외부 저장소의 기록된 Commit SHA 및 재현성 점검 |

## 관리 원칙

- GitHub에는 직접 작성한 Source, Custom Layer, Recipe, 설정 설명과 검증 기록을 관리합니다.
- Yocto 원본 Source, 다운로드 파일, 빌드 캐시, 이미지 등의 대용량 생성물은 커밋하지 않습니다.
- 변경·문제 해결 기록에는 **현상 → 원인 → 해결 → 검증**을 남깁니다.
- 실행하지 않은 명령은 확인 절차로 구분하고, 검증하지 않은 값은 추정하여 채우지 않습니다.
- 학교와 집의 실제 Checkout Commit 및 Host 환경은 재현 전에 다시 대조합니다.

## 현재 상태

Chapter 1에 기록된 `meta-raspberrypi` 등록, `MACHINE=raspberrypi4-64` 및 병렬도 설정 확인까지 완료했습니다. 다음 단계는 Chapter 2 학습이며, 이미지 빌드와 실장비 부팅은 아직 수행하지 않았습니다.
