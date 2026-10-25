# Yocto Raspberry Pi 4 Lab

**Yocto Project 6.0.4 (`wrynose`) 기반 Raspberry Pi 4B용 ARM64 Embedded Linux 이미지 빌드 및 실장비 검증 기록**

WSL2 환경에서 BitBake·OpenEmbedded 메타데이터를 분석하고, `core-image-minimal`을 빌드해 Raspberry Pi 4B에 배포했습니다. 이미지 생성에서 끝내지 않고 **UART 부팅·로그인, RootFS, Ethernet 연결, 외부 커널 모듈 삽입·제거**까지 실제 장비에서 확인한 과정과 문제 해결 근거를 기록합니다.

> **검증 환경:** **주 빌드 환경(센터)**에서 이미지 빌드와 실장비 부팅·통신 검증을 수행했습니다. **보조 개발 환경(집)**에서는 Recipe Parse 및 BitBake 메타데이터 분석을 수행했습니다.

## 검증 결과 한눈에 보기

| 영역 | 확인한 결과 | 상세 기록 |
|---|---|---|
| BitBake / Layer 분석 | Recipe 992개 Parse, 0 errors; Provider·Task 의존성·Image 설정 확인 (**집**) | [Chapter 2](docs/02-bitbake-layer-recipe.md) |
| ARM64 이미지 빌드 | `core-image-minimal` 최초 빌드 **4,025 Tasks 성공** (**센터**) | [Chapter 3](docs/03-arm64-image-build.md) |
| 이미지 산출물 | ARM64 Kernel `Image`, Raspberry Pi 4B DTB, RootFS, Wic 이미지 확인; `.wic.bz2` 압축 무결성 검사 통과 | [Chapter 3](docs/03-arm64-image-build.md) |
| 실장비 부팅 | Raspberry Pi 4B UART 콘솔 진입 및 `root` 로그인 성공 | [Chapter 5](docs/05-raspberrypi-boot.md) |
| 시스템 / 통신 | Linux `6.18.33-v8`, AArch64 커널, ext4 RootFS; Ethernet DHCP 및 외부 IP ping **4/4** | [Chapter 5](docs/05-raspberrypi-boot.md) |
| 외부 커널 모듈 | Yocto Recipe로 `hello_drv.ko` 빌드, 전송 및 `insmod`·`dmesg`·`rmmod` 검증 | [실장비 로그](docs/05-raspberrypi-boot.md) · [소스](examples/hello-drv/README.md) |

**주요 문제 해결:** 최초 이미지에서 부팅 후 `root` 로그인이 되지 않아 개발용 로그인 설정 Fragment를 적용하고 이미지를 증분 빌드·재기록해 로그인에 성공했습니다. 커널 메타데이터 Fetch 경고는 해당 Task의 최종 성공 여부를 로그로 구분했습니다. 원인과 확인되지 않은 부분은 각 Chapter에 별도로 명시했습니다.

## 시스템 구성과 작업 흐름

```text
Host (WSL2 / x86-64)
  ├─ Yocto Project 6.0.4 / BitBake 2.18.0
  ├─ OpenEmbedded-Core + Poky + meta-raspberrypi
  └─ MACHINE=raspberrypi4-64
          │
          ▼
   bitbake core-image-minimal
          │
          ├─ Linux Kernel Image + Device Tree Blob
          ├─ RootFS
          └─ Wic SD-card image (.wic.bz2)
                         │
                         ▼
              Raspberry Pi 4 Model B
                ├─ UART console / root login
                ├─ RootFS / kernel 확인
                ├─ Ethernet / DHCP / ping
                └─ hello_drv.ko 수동 적재·제거
```

**구분할 점:** `bitbake -p`의 Parse 성공은 전체 이미지 빌드 성공을 뜻하지 않습니다. 또한 `.wic.bz2`의 무결성 검사와 실장비 부팅 검증은 별개의 확인 단계입니다. Chapter 5의 커널 모듈은 수동으로 전송·적재했으며, 이미지에 기본 포함하거나 자동 로드한 결과는 아닙니다.

## 개발 환경

| 항목 | 센터 | 집 |
|---|---|---|
| Host OS | WSL2 Ubuntu 22.04 | WSL2 Ubuntu 26.04.1 LTS |
| CPU / RAM | 24 논리 CPU / 15GiB | 8 논리 CPU / 7.6GiB |
| `BB_NUMBER_THREADS` | `4` | `2` |
| `PARALLEL_MAKE` | `-j 4` | `-j 2` |
| 수행 범위 | 이미지 빌드·실장비 검증 | 환경 구성·Recipe Parse·메타데이터 분석 |

공통 Target 및 빌드 구성: **Raspberry Pi 4 Model B**, ARM64/AArch64, Yocto Project **6.0.4 (`wrynose`)**, `DISTRO=poky`, `MACHINE=raspberrypi4-64`, BSP Layer **`meta-raspberrypi`**.

두 Host의 경로·자원·Checkout SHA는 혼용하지 않습니다. 환경별 상세 설정은 [Chapter 1](docs/01-environment.md), [빌드 설정](configs/build-config.md), [소스 리비전](configs/source-revisions.md)을 참조하세요.

## 문서 바로가기

| 문서 | 핵심 내용 |
|---|---|
| [Chapter 1 — 환경 구성](docs/01-environment.md) | Setup, Locale 문제, BSP Layer 및 Machine 설정 |
| [Chapter 2 — BitBake·Layer·Recipe](docs/02-bitbake-layer-recipe.md) | 실제 명령·출력으로 분석한 Provider, Task 의존성, 설정 |
| [Chapter 3 — ARM64 Image Build](docs/03-arm64-image-build.md) | 4,025 Tasks 빌드, Fetch 경고 확인, 배포 산출물 검사 |
| [Chapter 5 — 실장비 부팅·검증](docs/05-raspberrypi-boot.md) | Wic, UART, root 로그인 문제 해결, Ethernet 및 외부 커널 모듈 실증 |
| [센터 환경 실행 근거](docs/logs/01-center-setup.md) | 환경 구성 오류 및 검증 기록 |
| [집 환경 실행 로그](docs/logs/01-home-setup.md) | Setup, Checkout SHA, Parse 성공 기록 |
| [외부 커널 모듈 코드](examples/hello-drv/README.md) | `hello_drv.c`, Makefile, `hello-drv_1.0.bb` 예제 소스 |
| [빌드 설정](configs/build-config.md) | Host별 설정값과 의미 |
| [소스 리비전](configs/source-revisions.md) | Checkout Commit SHA 및 재현성 확인 |

## 저장소 구조

```text
yocto-rpi4-lab/
├── README.md
├── configs/
│   ├── build-config.md
│   └── source-revisions.md
├── examples/
│   └── hello-drv/
│       ├── README.md
│       ├── hello-drv_1.0.bb
│       └── files/
│           ├── hello_drv.c
│           └── Makefile
└── docs/
    ├── 01-environment.md
    ├── 02-bitbake-layer-recipe.md
    ├── 03-arm64-image-build.md
    ├── 05-raspberrypi-boot.md
    └── logs/
        ├── 01-center-setup.md
        └── 01-home-setup.md
```

`examples/hello-drv/`에는 실장비에서 검증한 모듈의 소스 및 Recipe를 보관합니다. Yocto 전체 소스 트리나 빌드 산출물은 포함하지 않습니다.

## 검증 및 재현 기준

- **실행한 명령·관찰된 출력·해석·미검증 사항**을 구분합니다.
- 오류는 발생 현상과 후속 확인 결과를 기록하고, 증거가 없는 근본 원인은 단정하지 않습니다.
- 센터와 집의 OS·병렬도·빌드 경로 및 Git SHA를 분리해 기술합니다.
- 원본 Yocto Source, 다운로드 캐시, 이미지 및 빌드 산출물은 GitHub에 직접 커밋하지 않고, 생성 과정과 확인 결과를 문서화합니다.
- 실장비 검증에서 사용한 비밀번호 없는 root 로그인 허용은 **개발용 설정**이며, 제품용 보안 구성으로 사용하지 않습니다.
