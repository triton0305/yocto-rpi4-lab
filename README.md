# Yocto Raspberry Pi 4 Lab

Yocto Project를 활용하여 Raspberry Pi 4B용 Embedded Linux 시스템을 빌드하고 커스터마이징하는 실습 저장소입니다.

단순히 Linux 이미지를 생성하는 것뿐만 아니라 BitBake, OpenEmbedded, Layer, Recipe의 동작 원리를 이해하고, 직접 작성한 애플리케이션과 디바이스 드라이버를 통합하는 것을 목표로 합니다.

## 학습 목표

- BitBake, OpenEmbedded, Layer, Recipe 구조 및 동작 원리 이해
- Raspberry Pi 4B용 ARM64 Linux 이미지 빌드
- Linux Kernel 및 Root Filesystem 빌드 산출물 분석
- Custom Layer 및 Recipe 직접 작성
- C 애플리케이션과 Linux Device Driver 통합
- 실제 Raspberry Pi 4B에서 이미지 부팅 및 동작 검증

## 개발 환경

| 항목 | 구성 |
|---|---|
| Host | WSL2 Ubuntu (x86-64) |
| Target | Raspberry Pi 4 Model B |
| Architecture | AArch64 |
| Yocto Project | 6.0.4 (wrynose) |
| Distribution | Poky |
| Machine | raspberrypi4-64 |
| BSP Layer | meta-raspberrypi |

## 빌드 설정

WSL2 환경에서 메모리 부족을 방지하기 위해 빌드 병렬도를 제한했습니다.

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

- `BB_NUMBER_THREADS`: BitBake가 동시에 실행하는 작업 수 제한
- `PARALLEL_MAKE`: 개별 컴파일 작업의 병렬 실행 수 제한

## 학습 진행 현황

- [x] Chapter 1 — Yocto 개발 환경 구성
- [ ] Chapter 2 — BitBake · Layer · Recipe 구조
- [ ] Chapter 3 — 최소 Linux 이미지 빌드
- [ ] Chapter 4 — RootFS 및 빌드 산출물 분석
- [ ] Chapter 5 — Raspberry Pi 4B 부팅 검증
- [ ] Chapter 6 — Custom Layer 제작
- [ ] Chapter 7 — Custom Recipe 및 C 애플리케이션
- [ ] Chapter 8 — Kernel 및 Device Driver 통합
- [ ] Chapter 9 — 증분 빌드 · 의존성 · 오류 분석

## 프로젝트 구조

```text
yocto-rpi4-lab/
├── README.md
├── docs/
│   └── 01-environment.md
├── configs/
│   └── build-config.md
└── scripts/
```

추후 실습 진행에 따라 Custom Layer 및 Recipe 관련 디렉터리를 추가할 예정입니다.

## 문서

- `docs/01-environment.md` — 개발 환경 구성 및 검증 기록
- `configs/build-config.md` — 빌드 설정 및 변경 사항

## 저장소 관리 원칙

이 저장소에는 직접 작성한 소스 코드, 커스텀 설정, 실습 과정 및 검증 결과를 기록합니다.

Yocto 원본 소스, 다운로드된 패키지, 빌드 캐시 및 생성된 Linux 이미지 등 대용량 산출물은 Git 저장소에 포함하지 않습니다.

## 현재 상태

Yocto 6.0.4 개발 환경 구성과 Raspberry Pi 4B BSP Layer 등록을 완료했습니다.

현재 `MACHINE=raspberrypi4-64`, `DISTRO=poky` 설정이 적용되어 있으며, Linux 이미지 빌드와 실장비 부팅 검증은 아직 진행하지 않았습니다.

