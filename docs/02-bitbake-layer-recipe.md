# Chapter 2 — BitBake·Layer·Recipe 메타데이터 분석

> **관련 문서:** [Chapter 1 환경 구성](01-environment.md) · [Chapter 1 집 실행 로그](logs/01-home-setup.md) · [빌드 설정](../configs/build-config.md) · [Source SHA](../configs/source-revisions.md)

> **환경:** 이 장은 집 WSL2에서 확인한 메타데이터 분석을 기록한다. 병렬도 `2 / -j 2`는 [집 환경 구성 로그](logs/01-home-setup.md)의 `bitbake -e` 결과이며, 이 장에서 별도로 재조회한 값은 아니다.

**주제:** BitBake · Layer · Recipe · Provider · Task · Image · Configuration Fragment  
**실습 기간:** 2026-10-24 ~ 2026-10-25  
**대상 장비:** Raspberry Pi 4 Model B, ARM64 (AArch64)  
**결과:** Recipe Parse, Layer·Provider·Task 의존성 및 Image 설정 분석을 완료했다. 실제 이미지 빌드와 실장비 검증은 [ARM64 이미지 빌드](03-arm64-image-build.md) 및 [Raspberry Pi 부팅](05-raspberrypi-boot.md)에 기록했다.

> **증거 구분:** `실행 검증`은 명령의 출력, `파일 확인`은 원본 설정·Recipe 조회, `해석`은 해당 출력으로부터 도출한 기술적 설명을 뜻한다. 출력이 없는 항목은 관찰 사실로 취급하지 않는다. 긴 로그는 실행 위치·명령과 함께 핵심 부분을 발췌했다.

---

## 목차

- [환경·경로 기준](#0-환경과-경로-기준)
- [BitBake Parse 검증](#2-bitbake-파싱-및-실행-경로-검증)
- [Layer·Recipe 구조](#3-layer-구조와-recipe-탐색)
- [Provider 선택과 의존성](#5-provider와-최종-머신-기능-검증)
- [BusyBox Task 그래프](#7-busybox-task-목록과-실제-의존성-그래프)
- [Image Task와 설정](#8-image-생성-task-및-최종-이미지-설정)
- [Configuration Fragment](#9-yocto-60-configuration-fragment)
- [명령·출력 색인](#11-실습-명령-및-출력-추적-색인)

## 0. 환경과 경로 기준

### 0.1 시스템 및 빌드 설정

| 구분 | 실습 환경 / 확인값 |
|---|---|
| Host | Windows 11 + WSL2 Ubuntu 26.04 계열 (x86-64) |
| Target | Raspberry Pi 4 Model B, ARM64 |
| Yocto / DISTRO | 6.0.4 (`wrynose`) / `poky` |
| BitBake | `2.18.0` (Task 목록 출력에서 확인) |
| MACHINE | `raspberrypi4-64` |
| TARGET_SYS | `aarch64-poky-linux` |
| TUNE_FEATURES | `aarch64 crc cortexa72 nocrypto` |
| 빌드 병렬 설정 | `BB_NUMBER_THREADS = "2"`, `PARALLEL_MAKE = "-j 2"` (Chapter 1 **집** `bitbake -e` 검증값; Chapter 2에서 재조회하지 않음) |
| 활성 Layer | `core`, `yoctobsp`, `yocto`, `raspberrypi` |

다음 절대 경로를 이 문서 전체에서 사용한다.

```text
BUILD_DIR=/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
LAYERS_DIR=/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers
```

명령 실행 프롬프트가 반복적으로 표시한 **공통 실행 위치(CWD, Current Working Directory, 현재 작업 디렉터리)**는 아래와 같다.

```text
/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
```

**주의:** 이후 각 로그에서도 실행 위치를 적었다. `${BUILD_DIR}` 및 `${LAYERS_DIR}` 표기는 경로를 설명하기 위한 약칭이며, 실제 셸에 해당 변수가 설정되었다는 뜻은 아니다.

### 0.2 주요 디렉터리와 파일 경로

```text
~/study/rootfs/yocto/
└── bitbake-builds/
    └── poky-wrynose/
        ├── build/
        │   ├── init-build-env
        │   ├── conf/
        │   │   ├── bblayers.conf
        │   │   ├── toolcfg.conf
        │   │   └── local.conf          # 역할 및 기존 설정만 설명; 본 대화에서 전문을 읽지는 않음
        │   ├── cache/
        │   ├── tmp/
        │   ├── pn-buildlist            # bitbake -g busybox로 생성
        │   └── task-depends.dot       # bitbake -g busybox로 생성
        └── layers/
            ├── bitbake/bin/bitbake
            ├── openembedded-core/meta/
            │   ├── recipes-core/images/core-image-minimal.bb
            │   └── recipes-core/packagegroups/packagegroup-core-boot.bb
            ├── meta-yocto/
            │   ├── meta-poky/conf/distro/poky.conf
            │   └── meta-yocto-bsp/
            └── meta-raspberrypi/
                ├── conf/layer.conf
                ├── conf/machine/raspberrypi4-64.conf
                ├── conf/machine/include/rpi-base.inc
                ├── conf/machine/include/rpi-default-providers.inc
                └── recipes-*/...
```

---

## 1. 전체 그림 — Yocto가 Linux 이미지를 구성하는 과정

### 1.1 용어와 역할

| 용어 | 풀네임 / 한국어 뜻 | 이 실습에서의 역할 |
|---|---|---|
| Yocto Project | 임베디드 Linux 구축 프로젝트 | 전체 도구와 개발 체계 |
| OpenEmbedded-Core (OE-Core) | OpenEmbedded 핵심 메타데이터 | 공통 Recipe, Class, 설정 제공 |
| Poky | Yocto 참조 배포판 이름(약어 아님) | 배포판 정책 및 참조 구성 |
| BitBake | 빌드 실행 엔진(약어 아님) | 메타데이터 파싱, 의존성 해석, Task 실행 |
| BSP | Board Support Package / 보드 지원 패키지 | Raspberry Pi 하드웨어 지원 설정 |
| Layer | 메타데이터의 논리적 묶음 | 설정, Recipe, Class, 확장 파일 관리 |
| Recipe | 조리법에 비유한 `.bb` 빌드 명세 | 소프트웨어·이미지의 생성 방식을 정의 |
| Task | 개별 빌드 작업 | `do_fetch`, `do_compile`, `do_rootfs` 등 |
| RootFS | Root File System / 루트 파일시스템 | 최종 시스템의 `/` 아래 파일과 디렉터리 |

개념적인 처리 흐름:

```text
bblayers.conf ──→ Layer의 conf/layer.conf ──→ *.bb / *.bbappend 탐색
                                            │
 DISTRO, MACHINE, Fragment, local.conf ──────┤
                                            ▼
                                     BitBake 메타데이터 파싱
                                            ▼
                                  Provider / 의존성 / Task 결정
                                            ▼
                         소스 확보 → 빌드 → 패키징 → RootFS → 이미지
```

- **Kbuild/Make와 비교:** `make -j4`는 주로 특정 소프트웨어(예: Linux Kernel)의 빌드 규칙을 실행한다. BitBake는 Recipe 간 의존성을 포함해 운영체제 이미지 전체의 구축 작업을 관리한다.
- **Host/Target 구분:** WSL의 x86-64 호스트에서 ARM64용 실행 파일을 만드는 것은 Cross Compilation(교차 컴파일)이다.
- **파싱과 빌드는 별개:** Recipe를 모두 읽어도 `do_compile`이나 `do_rootfs`가 실행된 것은 아니다.

---

## 2. BitBake 파싱 및 실행 경로 검증

### 2.1 `bitbake -p`로 Recipe 파싱

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -p`
- **관찰 출력:**

```text
Loading cache: 100% ...
Loaded 0 entries from dependency cache.
Parsing recipes: 100% ... Time: 0:00:24
Parsing of 992 .bb files complete (0 cached, 992 parsed). 2013 targets, 73 skipped, 0 masked, 0 errors.
```

| 값 | 해석 |
|---|---|
| 992 `.bb` | 이 실행에서 파싱한 Recipe 파일 수 |
| 0 cached / 992 parsed | 이번 실행에서 캐시된 Recipe 항목을 재사용하지 않고 파싱 |
| 2013 targets | BitBake가 인식한 빌드 대상 수. 이미지 개수는 아님 |
| 73 skipped | 조건 등에 따라 건너뛴 항목 수. 오류 73개가 아님 |
| 0 masked / 0 errors | 마스킹된 Recipe 0, 파싱 오류 0 |

**확인한 결론:** `-p`는 파싱 후 종료한다. 이미지 생성은 실행하지 않았다.

### 2.2 BitBake 실행 파일 확인 및 셸 환경 문제

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `command -v bitbake`
- **관찰 출력:**

```text
/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/bitbake/bin/bitbake
```

앞선 시점에는 같은 디렉터리에서 `bitbake -p` 실행 시 `bitbake: command not found`가 한 차례 발생했다. 이후 재실행에서는 정상 동작했다.

- **학습한 원인 후보:** 새 셸에서는 BitBake 경로가 `PATH`에 없을 수 있다.
- **안내한 활성화 명령:** `source ./init-build-env` (실행 위치: `BUILD_DIR`)
- **확인 범위:** `source` 실행 자체의 출력은 확보되지 않았다. **다음 조회에서 BitBake가 정상 인식된 사실**을 확인했으며, 원인을 확정하지 않는다.
- **`source`의 의미:** 별도 자식 셸이 아니라 현재 Bash 셸에 환경변수 변경을 적용한다.

---

## 3. Layer 구조와 Recipe 탐색

### 3.1 활성 Layer 목록

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake-layers show-layers`
- **관찰 출력(경로는 줄바꿈 없이 표시):**

```text
layer       path                                                                  priority
core        /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta           5
yoctobsp    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-yocto-bsp      5
yocto       /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-poky           5
raspberrypi /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi                9
```

- `core`: 공통 소프트웨어 및 핵심 빌드 메타데이터.
- `yoctobsp`: 참조 보드용 BSP Layer. 등록되어 있다고 해당 보드를 선택한 것은 아님.
- `yocto`: `poky` 배포판 정책.
- `raspberrypi`: Raspberry Pi용 BSP.
- **Priority(우선순위):** 동일 Recipe 후보 등의 선택에 사용되는 Layer 우선순위. **실제 컴파일 순서가 아니다.**

### 3.2 `bblayers.conf` — 어떤 Layer를 읽을 것인가?

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/conf/bblayers.conf`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat conf/bblayers.conf`
- **관찰 파일 내용:**

```bitbake
BBLAYERS ?= " \
  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta \
  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-yocto-bsp \
  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-poky \
  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi \
  "
```

- `BBLAYERS`: 활성 Layer 경로 목록.
- `?=`: 이전에 정해진 값이 없으면 설정하는 기본값 할당.
- `\`: 설정 문자열을 여러 줄로 이어 작성.
- 이 파일에는 개별 `.bb` 파일 이름이 없다. Recipe 검색 규칙은 각 Layer의 `layer.conf` 등에서 가져온다.

### 3.3 `meta-raspberrypi/conf/layer.conf` — Layer 내부의 Recipe 탐색 규칙

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi/conf/layer.conf`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/meta-raspberrypi/conf/layer.conf`
- **관찰한 주요 원문:**

```bitbake
BBPATH .= ":${LAYERDIR}"

BBFILES += "${LAYERDIR}/recipes*/*/*.bb \
            ${LAYERDIR}/recipes*/*/*.bbappend"

BBFILE_COLLECTIONS += "raspberrypi"
BBFILE_PATTERN_raspberrypi := "^${LAYERDIR}/"
BBFILE_PRIORITY_raspberrypi = "9"
LAYERSERIES_COMPAT_raspberrypi = "wrynose"
LAYERDEPENDS_raspberrypi = "core"

LICENSE_PATH += "${LAYERDIR}/files/custom-licenses"
```

추가로 같은 파일에 `BBFILES_DYNAMIC`이 있으며, `openembedded-layer`, `networking-layer`, `qt5-layer`, `multimedia-layer`, `meta-python` 등의 컬렉션이 있을 때 해당 확장 Recipe/Append를 찾아 활성화하도록 정의되어 있었다. 또한 `DEFAULT_TEST_SUITES:remove:rpi`, `:append:rpi` 설정도 존재했다.

| 변수 | 기능 |
|---|---|
| `BBPATH` | 설정·클래스 등의 검색 경로 확장 |
| `BBFILES` | `.bb`와 `.bbappend` 파일 탐색 패턴 |
| `BBFILE_COLLECTIONS` | 컬렉션 이름 `raspberrypi` 등록 |
| `BBFILE_PATTERN_raspberrypi` | 해당 컬렉션에 속한 파일의 경로 패턴 |
| `BBFILE_PRIORITY_raspberrypi` | 우선순위 `9`의 직접적인 근거 |
| `LAYERSERIES_COMPAT_raspberrypi` | `wrynose` 호환 선언 |
| `LAYERDEPENDS_raspberrypi` | `core` Layer에 의존 |
| `BBFILES_DYNAMIC` | 조건에 맞는 다른 Layer가 존재할 때 확장 파일 탐색 |

`.bb`는 Recipe 본문, `.bbappend`는 기존 Recipe에 적용하는 확장 파일이다. **탐색 경로에 들어 있다고 모든 Recipe가 이미지에 설치되는 것은 아니다.**

### 3.4 실제 Raspberry Pi Recipe 10개 확인

- **탐색 대상 경로:** `LAYERS_DIR/meta-raspberrypi/recipes*/*/*.bb`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `ls ../layers/meta-raspberrypi/recipes*/*/*.bb | head -n 10`
- **관찰 출력:**

```text
../layers/meta-raspberrypi/recipes-bsp/armstubs/armstubs.bb
../layers/meta-raspberrypi/recipes-bsp/bootfiles/rpi-bootfiles.bb
../layers/meta-raspberrypi/recipes-bsp/bootfiles/rpi-cmdline.bb
../layers/meta-raspberrypi/recipes-bsp/bootfiles/rpi-config_git.bb
../layers/meta-raspberrypi/recipes-bsp/gpio-shutdown/gpio-shutdown.bb
../layers/meta-raspberrypi/recipes-bsp/rpi-eeprom/rpi-eeprom_git.bb
../layers/meta-raspberrypi/recipes-bsp/rpi-u-boot-scr/rpi-u-boot-scr.bb
../layers/meta-raspberrypi/recipes-connectivity/pi-bluetooth/pi-bluetooth_0.1.19.bb
../layers/meta-raspberrypi/recipes-core/images/rpi-test-image.bb
../layers/meta-raspberrypi/recipes-core/packagegroups/packagegroup-rpi-test.bb
```

- **학습 해석:** 부팅 관련 Recipe, Bluetooth 관련 Recipe, Raspberry Pi 테스트 이미지 Recipe가 탐색됐다.
- **검증 한계:** 이 단계에서는 **파일 이름만 확인**했다. 해당 Recipe 내부의 정확한 설정 및 실제 빌드 여부는 확인하지 않았다.
- **기술적 연결:** `rpi-u-boot-scr.bb`는 U-Boot 스크립트 관련 Recipe이며, 이 파일의 존재만으로 실제 부팅 체인에서 U-Boot 사용 여부를 확정할 수는 없다.

---

## 4. DISTRO와 MACHINE 설정 분리

### 4.1 두 설정 파일의 존재 검증

- **실행 위치:** `BUILD_DIR`
- **실행 명령:**

```bash
ls -l \
  ../layers/meta-yocto/meta-poky/conf/distro/poky.conf \
  ../layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf
```

- **관찰 출력:**

```text
-rw-r--r-- 1 triton triton 1163 Oct 23 00:23 ../layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf
-rw-r--r-- 1 triton triton 2226 Oct 23 00:16 ../layers/meta-yocto/meta-poky/conf/distro/poky.conf
```

| 구분 | DISTRO | MACHINE |
|---|---|---|
| 변수 | `DISTRO = "poky"` | `MACHINE = "raspberrypi4-64"` |
| 파일 | `LAYERS_DIR/meta-yocto/meta-poky/conf/distro/poky.conf` | `LAYERS_DIR/meta-raspberrypi/conf/machine/raspberrypi4-64.conf` |
| 역할 | 배포판의 정책·기본 설정 | CPU, Device Tree, 커널/부팅 등 하드웨어 설정 |

### 4.2 `poky.conf` — 배포판 정책

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-poky/conf/distro/poky.conf`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/meta-yocto/meta-poky/conf/distro/poky.conf`
- **터미널에서 조회한 설정 원문:**

```bitbake
DISTRO = "poky"
DISTRO_NAME = "Poky (Yocto Project Reference Distro)"
DISTRO_VERSION = "6.0.4"
DISTRO_CODENAME = "wrynose"
SDK_VENDOR = "-pokysdk"
TARGET_VENDOR = "-poky"

POKY_DEFAULT_DISTRO_FEATURES = ""
POKY_DEFAULT_EXTRA_RDEPENDS = "packagegroup-core-boot"
POKY_DEFAULT_EXTRA_RRECOMMENDS = "kernel-module-af-packet"
DISTRO_FEATURES ?= "${POKY_DEFAULT_DISTRO_FEATURES}"

PREFERRED_VERSION_linux-yocto ?= "6.18%"
PREFERRED_VERSION_linux-yocto-rt ?= "6.18%"

DISTRO_EXTRA_RDEPENDS += "${POKY_DEFAULT_EXTRA_RDEPENDS}"
DISTRO_EXTRA_RRECOMMENDS += "${POKY_DEFAULT_EXTRA_RRECOMMENDS}"
PACKAGE_CLASSES ?= "package_rpm"

INHERIT += "poky-sanity"
require conf/distro/include/poky-world-exclude.inc
BB_SIGNATURE_HANDLER ?= "OEEquivHash"
BB_HASHSERVE ??= "auto"
POKY_INIT_MANAGER = "sysvinit"
INIT_MANAGER ?= "${POKY_INIT_MANAGER}"

KERNEL_EXTRA_FEATURES:append = " features/debug/debug-kernel.scc"
```

같은 파일에 `SDK_VERSION`, `SDK_NAME`, `SDKPATHINSTALL`, `MAINTAINER`, `LOCALCONF_VERSION`, `SANITY_TESTED_DISTROS` 등도 존재했다. 호스트 목록에는 `ubuntu-26.04`가 포함되어 있었다.

- `SDK`: Software Development Kit / 소프트웨어 개발 키트. 여기서는 SDK 식별자와 설치 경로를 위한 설정.
- `PACKAGE_CLASSES ?= "package_rpm"`: 기본 패키지 생성 형식은 RPM 계열. **타깃에 rpm CLI가 자동 설치된다는 뜻이 아니다.**
- `POKY_INIT_MANAGER = "sysvinit"`: 기본 사용자 공간 초기화 시스템으로 sysvinit을 선택하도록 설정.
- `PREFERRED_VERSION_linux-yocto ?= "6.18%"`: `linux-yocto` Recipe의 선호 버전 패턴. **현재 Raspberry Pi 커널 버전이 6.18이라는 뜻이 아니다.**
- `INHERIT += "poky-sanity"`: 빌드 환경 점검용 공통 Class 사용.

### 4.3 `raspberrypi4-64.conf` — 하드웨어 설정

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf`
- **관찰 원문:**

```bitbake
MACHINEOVERRIDES =. "raspberrypi4:"
MACHINE_FEATURES += "pci"
MACHINE_EXTRA_RRECOMMENDS += "\
    linux-firmware-rpidistro-bcm43455 \
    bluez-firmware-rpidistro-bcm4345c0-hcd \
    linux-firmware-rpidistro-bcm43456 \
    bluez-firmware-rpidistro-bcm4345c5-hcd \
"

DEFAULTTUNE = "cortexa72-nocrypto"
require conf/machine/include/arm/armv8a/tune-cortexa72.inc
include conf/machine/include/rpi-base.inc

RPI_KERNEL_DEVICETREE = " \
    broadcom/bcm2711-rpi-4-b.dtb \
    broadcom/bcm2711-rpi-400.dtb \
    broadcom/bcm2711-rpi-cm4.dtb \
    broadcom/bcm2711-rpi-cm4s.dtb \
"

SDIMG_KERNELIMAGE ?= "kernel8.img"
SERIAL_CONSOLES ?= "115200;ttyS0"
UBOOT_MACHINE = "rpi_arm64_config"
VC4DTBO ?= "vc4-kms-v3d"
KERNEL_IMAGETYPE_UBOOT ?= "Image"
KERNEL_IMAGETYPE_DIRECT ?= "Image"
KERNEL_BOOTCMD ?= "booti"
ARMSTUB ?= "armstub8-gic.bin"
```

| 변수 | 이해한 의미 |
|---|---|
| `MACHINEOVERRIDES =. "raspberrypi4:"` | Raspberry Pi 4 계열 공통 Override 이름을 앞에 붙임 |
| `DEFAULTTUNE` | Cortex-A72용 컴파일 최적화 선택 |
| `RPI_KERNEL_DEVICETREE` | 지원 보드의 Device Tree Blob(DTB) 파일 이름 |
| `SDIMG_KERNELIMAGE` | SD 이미지에 배치할 커널 파일 이름 기본값 |
| `SERIAL_CONSOLES` | 115200 bps, `ttyS0` 시리얼 콘솔 기본값 |
| `UBOOT_MACHINE` | U-Boot용 Raspberry Pi ARM64 보드 설정 |
| `KERNEL_IMAGETYPE_*` | 커널 이미지 형식 기본값 `Image` |
| `KERNEL_BOOTCMD` | U-Boot의 ARM64 커널 부팅 명령 `booti` |
| `ARMSTUB` | 초기 ARM 부팅 Stub 설정 |

- `DTB`: Device Tree Blob / 장치 트리 바이너리. Linux Kernel에 하드웨어 구성을 전달한다.
- `UART`: Universal Asynchronous Receiver/Transmitter / 범용 비동기 송수신기. 여기서는 시리얼 콘솔과 연결된다.
- `U-Boot`를 사용하는 설정값이 **존재한다**고 해서 실제 이미지가 U-Boot로 부팅하도록 확정된 것은 아니다.
- `MACHINE_EXTRA_RRECOMMENDS`에 Wi-Fi/ Bluetooth 펌웨어 패키지가 등장하지만 최소 이미지에 반드시 포함된다고 단정하면 안 된다.

### 4.4 `require`와 `include` 구분

관찰 파일: `LAYERS_DIR/meta-raspberrypi/conf/machine/raspberrypi4-64.conf`

```bitbake
require conf/machine/include/arm/armv8a/tune-cortexa72.inc
include conf/machine/include/rpi-base.inc
```

- `require`: 참조한 파일이 없으면 파싱 오류.
- `include`: 파일이 없으면 건너뛸 수 있음.
- **중요:** “CPU 설정이면 `require`, 공통 설정이면 `include`”라는 규칙은 없다. **없을 때 오류로 처리할 것인가**가 차이다.

### 4.5 `rpi-base.inc` — Raspberry Pi 공통 설정

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi/conf/machine/include/rpi-base.inc`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `sed -n '1,100p' ../layers/meta-raspberrypi/conf/machine/include/rpi-base.inc`
- **직접 확인한 내용 중 핵심 부분:**

```bitbake
include conf/machine/include/rpi-default-settings.inc
include conf/machine/include/rpi-default-versions.inc
include conf/machine/include/rpi-default-providers.inc

SOC_FAMILY = "rpi"
include conf/machine/include/soc-family.inc

IMAGE_FSTYPES ?= "tar.bz2 ext3 wic.bz2 wic.bmap"
WKS_FILE ?= "sdimage-raspberrypi.wks"
```

출력에는 `XSERVER` 조건식과 수십 개의 Device Tree Overlay 목록도 있었다. 그중 확인한 예시는 다음과 같다.

```text
overlays/i2c-gpio.dtbo
overlays/mcp2515-can0.dtbo
overlays/mcp2515-can1.dtbo
overlays/uart0.dtbo
overlays/uart1.dtbo
overlays/vc4-kms-v3d.dtbo
```

- **Overlay:** 기존 Device Tree 구성을 확장·변경하는 데이터. 파일 이름이 목록에 있다고 해당 외부 장치가 실제 연결·활성화된 것은 아니다.
- `mcp2515-can0.dtbo` 등은 CAN(Controller Area Network / 차량·산업 장치 통신망) 관련 하드웨어와 연결되는 학습 포인트다.
- `WKS_FILE`은 디스크 파티션 배치를 기술한 **Wic Kickstart 설정 파일** 이름을 지정한다.

> **확인 범위:** `sed -n '1,100p'`는 `rpi-base.inc`의 처음 100줄만 표시한다. 그 이후에 있을 수 있는 `MACHINE_FEATURES_DEFAULTS:append` / `DISABLE_VC4GRAPHICS` 관련 구문은 이 명령으로 확인되지 않았다. 최종 `MACHINE_FEATURES` 및 EGL Provider 값은 아래 `bitbake -e` 조회 결과로 검증했다.

---

## 5. Provider와 최종 머신 기능 검증

### 5.1 `rpi-default-providers.inc` 원문

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi/conf/machine/include/rpi-default-providers.inc`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/meta-raspberrypi/conf/machine/include/rpi-default-providers.inc`
- **관찰 원문:**

```bitbake
# RaspberryPi BSP default providers
PREFERRED_PROVIDER_virtual/kernel ??= "linux-raspberrypi"
PREFERRED_PROVIDER_virtual/xserver ?= "xserver-xorg"
PREFERRED_PROVIDER_virtual/egl ?= "${@bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "userland", d)}"
PREFERRED_PROVIDER_virtual/libgles2 ?= "${@bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "userland", d)}"
PREFERRED_PROVIDER_virtual/libgl ?= "${@bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "mesa-gl", d)}"
PREFERRED_PROVIDER_virtual/mesa ?= "${@bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "mesa-gl", d)}"
PREFERRED_PROVIDER_virtual/libgbm ?= "${@bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "mesa-gl", d)}"
PREFERRED_PROVIDER_jpeg ?= "jpeg"
PREFERRED_PROVIDER_virtual/libomxil ?= "userland"
VIRTUAL-RUNTIME_libomxil = "userland"
PREFERRED_PROVIDER_u-boot-default-script ??= "rpi-u-boot-scr"
```

**Provider(제공자)**는 `virtual/kernel`처럼 추상적인 기능·대상을 실제 어느 Recipe가 제공할지 선택하는 개념이다.

- `PREFERRED_PROVIDER_virtual/kernel`: 커널의 선호 Recipe.
- `PREFERRED_PROVIDER_virtual/egl`: EGL 인터페이스를 제공할 소프트웨어 선택.
- `PREFERRED_PROVIDER_u-boot-default-script`: U-Boot의 기본 부팅 스크립트 Recipe 선호값.
- **Provider의 선택은 기능 활성화와 다르다.** 특히 U-Boot 스크립트의 Provider를 정했다고 U-Boot 사용이 자동으로 켜지는 것이 아니다.

### 5.2 `MACHINE_FEATURES`와 EGL Provider 최종값

- **실행 위치:** `BUILD_DIR` (스크린샷에 프롬프트로 표시)
- **실행 명령:** `bitbake -e | grep -E '^(MACHINE_FEATURES|PREFERRED_PROVIDER_virtual/egl)='`
- **관찰 출력(스크린샷에서 확인):**

```text
MACHINE_FEATURES=" pci alsa apm bluetooth ext2 keyboard qemu-usermode screen sdio touchscreen usbhost vc4graphics vfat wifi"
PREFERRED_PROVIDER_virtual/egl="mesa"
```

> 표시 줄이 길어 원본 터미널에서는 `MACHINE_FEATURES`가 다음 줄로 이어져 보였다. 위에는 한 줄로 합쳐 적었다.

**해석:**

1. `MACHINE_FEATURES`에 `vc4graphics`가 **실제로 포함**되어 있다.
2. `bb.utils.contains("MACHINE_FEATURES", "vc4graphics", "mesa", "userland", d)`의 조건이 참인 쪽이 된다.
3. 최종 선호 Provider가 `mesa`로 계산됐다는 것이 출력으로 확인됐다.

용어:

- `GPU`: Graphics Processing Unit / 그래픽 처리 장치.
- `VC4`: VideoCore IV 계열 그래픽 하드웨어 기술.
- `EGL`: Embedded-System Graphics Library / 그래픽 프로그램의 렌더링 환경·화면 시스템을 연결하는 인터페이스.
- `OpenGL ES`: Open Graphics Library for Embedded Systems / 임베디드용 그래픽 API(Application Programming Interface, 응용 프로그램 인터페이스).
- `Mesa`: Linux용 오픈소스 그래픽 API 구현체(약어가 아닌 프로젝트명).
- `userland`: 여기서는 Raspberry Pi의 특정 레거시 그래픽 라이브러리 구현을 가리키는 Recipe/소프트웨어 이름이며, 일반적 의미의 “모든 사용자 공간”과 구분한다.

**주의:** `vc4graphics`가 있다는 사실이 그래픽 프로그램을 설치했다거나 디스플레이 출력을 검증했다는 뜻은 아니다.

### 5.3 Kernel Provider 최종값

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -e | grep '^PREFERRED_PROVIDER_virtual/kernel='`
- **관찰 출력:**

```text
PREFERRED_PROVIDER_virtual/kernel="linux-raspberrypi"
```

**해석:** Poky에 `linux-yocto` 선호 버전이 정의되어 있더라도, 현재 Raspberry Pi BSP에서는 `linux-raspberrypi`가 커널의 선호 Provider로 계산됐다. **실제 컴파일된 Kernel 버전은 아직 미검증**이다.

---

## 6. Image Recipe와 Runtime Packagegroup

### 6.1 `core-image-minimal.bb` 원문

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta/recipes-core/images/core-image-minimal.bb`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/openembedded-core/meta/recipes-core/images/core-image-minimal.bb`
- **관찰 원문:**

```bitbake
SUMMARY = "A small image just capable of allowing a device to boot."

IMAGE_INSTALL = "packagegroup-core-boot ${CORE_IMAGE_EXTRA_INSTALL}"

IMAGE_LINGUAS = " "

LICENSE = "MIT"

inherit core-image

IMAGE_ROOTFS_SIZE ?= "8192"
IMAGE_ROOTFS_EXTRA_SPACE:append = "${@bb.utils.contains("DISTRO_FEATURES", "systemd", " + 4096", "", d)}"
```

- `IMAGE_INSTALL`: RootFS에 넣을 설치 패키지 목록의 출발점.
- `packagegroup-core-boot`: 필수 부팅 패키지를 묶은 packagegroup.
- `CORE_IMAGE_EXTRA_INSTALL`: 추가로 설치할 패키지를 지정할 수 있는 확장 변수.
- `IMAGE_LINGUAS = " "`: 언어별 번역 패키지 추가를 최소화.
- `LICENSE = "MIT"`: Recipe의 라이선스 선언.
- `inherit core-image`: 공통 이미지 구성 Class(`core-image.bbclass` 등)의 기능을 적용.
- `IMAGE_ROOTFS_SIZE ?= "8192"`: RootFS 최소 크기 계산에 사용할 기본값(일반적으로 KiB 단위). **완성 이미지가 8MiB로 고정된다는 뜻은 아니다.**
- `IMAGE_ROOTFS_EXTRA_SPACE:append`: 배포판 기능에 `systemd`가 포함되면 4096KiB의 여유 공간 추가.

### 6.2 `packagegroup-core-boot.bb` 원문

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta/recipes-core/packagegroups/packagegroup-core-boot.bb`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat ../layers/openembedded-core/meta/recipes-core/packagegroups/packagegroup-core-boot.bb`
- **관찰한 주요 원문:**

```bitbake
SUMMARY = "Minimal boot requirements"
DESCRIPTION = "The minimal set of packages required to boot the system"
PACKAGE_ARCH = "${MACHINE_ARCH}"
inherit packagegroup

EFI_PROVIDER ??= "grub-efi"
SYSVINIT_SCRIPTS = "${@bb.utils.contains('MACHINE_FEATURES', 'rtc', '${VIRTUAL-RUNTIME_base-utils-hwclock}', '', d)} \
                    modutils-initscripts \
                    ${VIRTUAL-RUNTIME_initscripts} \
                   "

RDEPENDS:${PN} = "\
    base-files \
    base-passwd \
    ${VIRTUAL-RUNTIME_base-utils} \
    ${@bb.utils.contains("DISTRO_FEATURES", "sysvinit", "${SYSVINIT_SCRIPTS}", "", d)} \
    ${@bb.utils.contains("MACHINE_FEATURES", "keyboard", "${VIRTUAL-RUNTIME_keymaps}", "", d)} \
    ${@bb.utils.contains("MACHINE_FEATURES", "efi", "${EFI_PROVIDER} kernel", "", d)} \
    netbase \
    ${VIRTUAL-RUNTIME_login_manager} \
    ${VIRTUAL-RUNTIME_init_manager} \
    ${VIRTUAL-RUNTIME_dev_manager} \
    ${VIRTUAL-RUNTIME_update-alternatives} \
    ${MACHINE_ESSENTIAL_EXTRA_RDEPENDS}"

RRECOMMENDS:${PN} = "\
    ${VIRTUAL-RUNTIME_base-utils-syslog} \
    ${MACHINE_ESSENTIAL_EXTRA_RRECOMMENDS} \
    ${@bb.utils.contains("DISTRO_FEATURES", "sysvinit", "init-ifupdown", "", d)} \
    ${@bb.utils.contains("DISTRO_FEATURES", "sysvinit pni-names", "ifupdown", "", d)} \
    "
```

- `PN`: Recipe 이름(Recipe Name) 변수. 대부분의 단순 Recipe에서 기본 패키지 이름도 `PN`을 따른다.
- `RDEPENDS`: Runtime Dependencies / 실행 시 필요한 필수 패키지 의존성.
- `RRECOMMENDS`: Runtime Recommendations / 실행 시 권장 패키지 의존성. 기본 설정에서는 설치 대상으로 들어갈 수 있다.
- `MACHINE_ESSENTIAL_EXTRA_RDEPENDS` / `...RRECOMMENDS`: 머신별로 필수적인 런타임 패키지를 추가하는 통로.
- EFI: Extensible Firmware Interface / 확장 펌웨어 인터페이스. 이 Recipe에서는 머신 기능에 `efi`가 있을 때 추가 의존성 지정.

### 6.3 `RDEPENDS` / `RRECOMMENDS` 최종값

- **실행 위치:** `BUILD_DIR`
- **실행 명령:**

```bash
bitbake -e packagegroup-core-boot | grep -E '^R(DEPENDS|RECOMMENDS):packagegroup-core-boot='
```

- **관찰 출력:**

```text
RDEPENDS:packagegroup-core-boot="    base-files     base-passwd     busybox                          modutils-initscripts                     initscripts                         keymaps          netbase     busybox     sysvinit     udev     update-alternatives-opkg     "
RRECOMMENDS:packagegroup-core-boot="    busybox-syslog             init-ifupdown          "
```

**확인된 필수 패키지:** `base-files`, `base-passwd`, `busybox`, `modutils-initscripts`, `initscripts`, `keymaps`, `netbase`, `sysvinit`, `udev`, `update-alternatives-opkg`.

**확인된 권장 패키지:** `busybox-syslog`, `init-ifupdown`.

- `busybox`는 기본 명령어와 로그인 역할을 서로 다른 변수에서 참조하여 출력에 두 번 등장했으나 두 번 설치한다는 의미는 아니다.
- `udev`는 사용자 공간 장치 관리자이며 커널 장치 이벤트 및 `/dev` 관리와 관련된다.
- `sysvinit`는 System V Init(시스템 초기화 관리자).
- `init-ifupdown`은 네트워크 인터페이스 초기화용 구성 요소이지, Wi-Fi 인증·연결 도구가 자동으로 설치됐다는 근거는 아니다.

### 6.4 가상 런타임 변수의 최종값

- **실행 위치:** `BUILD_DIR`
- **실행 명령:**

```bash
bitbake -e packagegroup-core-boot | \
  grep -E '^VIRTUAL-RUNTIME_(base-utils|login_manager|init_manager|dev_manager)='
```

- **관찰 출력:**

```text
VIRTUAL-RUNTIME_base-utils="busybox"
VIRTUAL-RUNTIME_dev_manager="udev"
VIRTUAL-RUNTIME_init_manager="sysvinit"
VIRTUAL-RUNTIME_login_manager="busybox"
```

**결론:** 이번 빌드 설정에서 기본 도구 및 로그인은 BusyBox, 장치 관리는 udev, 시스템 초기화는 sysvinit을 사용하도록 선택했다.

### 6.5 ‘Wi-Fi 없는 최소 Linux’와의 관계

앞서 다른 명령에서 `MACHINE_FEATURES`의 `wifi`와 머신 설정의 펌웨어 권장 패키지를 확인했지만, **그 사실만으로 `core-image-minimal`에 Wi-Fi 연결 도구가 설치된다고 결론 내릴 수는 없다.**

구분해야 하는 계층:

1. `MACHINE_FEATURES`의 `wifi`: 머신이 가진/지원하는 하드웨어 기능을 메타데이터에 표시.
2. Kernel Driver: 커널이 Wi-Fi 장치를 제어하기 위한 코드.
3. Firmware: 무선 칩 내부 동작에 필요한 바이너리 등.
4. 연결 관리 프로그램: `wpa_supplicant` 등의 인증·연결 도구.
5. RootFS 설치 결과: 최종 이미지에서 실제 파일·패키지 존재 여부.

이번에 조회한 **`packagegroup-core-boot`의 직접 의존성**에는 `wpa-supplicant`가 나타나지 않았다. 그러나 패키지 간 간접 의존성 및 실제 RootFS 전체 패키지 목록은 아직 확인하지 않았으므로 “Wi-Fi 관련 요소가 완전히 없다”는 결론도 내리지 않는다.

---

## 7. BusyBox Task 목록과 실제 의존성 그래프

### 7.1 BusyBox Task 열거

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -c listtasks busybox`
- **관찰된 빌드 설정:**

```text
BB_VERSION           = "2.18.0"
BUILD_SYS            = "x86_64-linux"
NATIVELSBSTRING      = "ubuntu-26.04"
TARGET_SYS           = "aarch64-poky-linux"
MACHINE              = "raspberrypi4-64"
SDKMACHINE           = "x86_64"
DISTRO               = "poky"
DISTRO_VERSION       = "6.0.4"
TUNE_FEATURES        = "aarch64 crc cortexa72 nocrypto"
```

- **주요 Task(사용자 출력에서 발췌):**

| Task | 역할 |
|---|---|
| `do_fetch` | 소스 코드 확보 |
| `do_unpack` | 다운로드 소스 압축 해제/작업 디렉터리에 배치 |
| `do_patch` | 소스 수정 사항 적용 |
| `do_configure` | 컴파일 설정 준비 |
| `do_compile` | 실제 컴파일 |
| `do_install` | 임시 설치 영역에 파일 배치 |
| `do_package` | 설치 파일을 패키지로 분류 |
| `do_package_write_rpm` | RPM 패키지 출력 |
| `do_prepare_recipe_sysroot` | 해당 Recipe용 빌드 의존 파일 준비 |
| `do_populate_sysroot` | 다른 Recipe가 사용할 개발 파일 제공 |
| `do_build` | Recipe의 기본 빌드 종착 Task |
| `do_listtasks` | Task 목록 출력 |
| `do_*_setscene` | sstate 캐시 복원용 Task 유형 |

출력에 `do_configure_ptest_base`, `do_compile_ptest_base`, `do_install_ptest_base`, `do_package_qa`, `do_packagedata`, `do_create_spdx`, `do_create_recipe_sbom`, `do_populate_lic`, `do_devshell`, `do_menuconfig` 등도 있었다.

- `ptest`: Package Test / 타깃 시스템에서 실행할 수 있는 패키지 테스트 기능.
- `sstate`: Shared State / 이전 Task 결과물을 재사용하기 위한 공유 상태 캐시.
- `SPDX`: Software Package Data Exchange / 소프트웨어 구성·라이선스 정보를 표현하는 표준.
- `SBOM`: Software Bill of Materials / 소프트웨어 구성 요소 명세서.

**실행 상태:** 명령 끝에는 `Tasks Summary: Attempted 1 tasks ... all succeeded.`가 표시됐다. 이는 **`do_listtasks`만 실행했다**는 뜻이며 BusyBox를 컴파일했다는 뜻이 아니다.

**부수적 이벤트:** 최초에는 `uninative` 보조 구성 요소를 다운로드한다는 메시지가 나타났다. 이는 호스트에서 동작할 네이티브 도구 환경을 지원하기 위한 것으로, 다운로드 성공 여부는 이후 Task 목록 정상 종료 사실과 구별해 기록한다.

### 7.2 `bitbake -g busybox`로 의존성 파일 생성

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -g busybox`
- **관찰 출력:**

```text
Loaded 2013 entries from dependency cache.
NOTE: Resolving any missing task queue dependencies
NOTE: PN build list saved to 'pn-buildlist'
NOTE: Task dependencies saved to 'task-depends.dot'
```

- **생성 파일 절대 경로 1:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/pn-buildlist` — 빌드 의존 Recipe 목록.
- **생성 파일 절대 경로 2:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/task-depends.dot` — Task 의존성 그래프(DOT 형식).
- `DOT`: Graphviz에서 사용하는 그래프 기술 형식(여기서는 별도 약어로 풀지 않음).
- **이번 명령으로 실제 컴파일은 하지 않았다.**

### 7.3 `do_compile`의 직접 의존성

- **읽은 파일 경로:** `BUILD_DIR/task-depends.dot`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `grep -F '"busybox.do_compile" ->' task-depends.dot`
- **관찰 출력:**

```dot
"busybox.do_compile" -> "busybox.do_configure"
"busybox.do_compile" -> "busybox.do_configure_ptest_base"
```

DOT 파일의 `A -> B`는 이 경우 **A가 B에 의존**한다는 의미다. 실행 준비 순서로는 `B`의 조건 충족 후 `A`가 가능해진다. `do_configure_ptest_base`는 테스트 관련 설정 작업이다.

### 7.4 `do_configure`의 직접 의존성

- **읽은 파일 경로:** `BUILD_DIR/task-depends.dot`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `grep -F '"busybox.do_configure" ->' task-depends.dot | head -n 15`
- **관찰 출력:**

```dot
"busybox.do_configure" -> "busybox.do_deploy_source_date_epoch"
"busybox.do_configure" -> "busybox.do_patch"
"busybox.do_configure" -> "busybox.do_prepare_recipe_sysroot"
```

| Task | 의미 |
|---|---|
| `do_deploy_source_date_epoch` | 재현 가능한 결과를 위해 기준 시간 정보 준비 |
| `do_patch` | 패치 적용 |
| `do_prepare_recipe_sysroot` | 이 Recipe의 빌드에 필요한 파일들을 준비 |

`Sysroot`는 교차 컴파일에 필요한 헤더·라이브러리 등을 모아둔 빌드용 파일 계층이다. 최종 장치의 `/` RootFS와 혼동하지 않는다.

### 7.5 `do_prepare_recipe_sysroot`의 Recipe 간 의존성

- **읽은 파일 경로:** `BUILD_DIR/task-depends.dot`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:**

```bash
grep -F '"busybox.do_prepare_recipe_sysroot" ->' \
  task-depends.dot | head -n 15
```

- **관찰 출력:**

```dot
"busybox.do_prepare_recipe_sysroot" -> "busybox.do_fetch"
"busybox.do_prepare_recipe_sysroot" -> "gcc-cross-aarch64.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "gcc-runtime.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "glibc.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "initscripts.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "kern-tools-native.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "libxcrypt.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "opkg-utils.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "pseudo-native.do_populate_sysroot"
"busybox.do_prepare_recipe_sysroot" -> "update-rc.d.do_populate_sysroot"
```

주요 구성:

- `gcc-cross-aarch64`: Host(x86-64)에서 실행하여 Target(ARM64) 코드를 생성할 크로스 컴파일러.
- `glibc`: GNU C Library / GNU C 표준 라이브러리 구현.
- `gcc-runtime`: GCC 실행 지원 라이브러리.
- `kern-tools-native`: 빌드 PC에서 실행하는 커널 관련 도구.
- `libxcrypt`: 암호 해시 관련 라이브러리.
- `opkg-utils`, `update-rc.d`, `pseudo-native`, `initscripts`: 빌드·패키징·초기화 등을 지원하는 구성 요소.

**핵심:** 다른 Recipe의 `do_populate_sysroot` 결과가 준비되어야 BusyBox의 전용 Sysroot 구성이 가능하다. `native`는 호스트에서 실행하는 도구를 가리키고, `cross`는 호스트에서 타깃용 결과물을 생성하는 도구를 가리킨다.

### 7.6 BusyBox `DEPENDS` 최종값

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -e busybox | grep '^DEPENDS='`
- **관찰 출력:**

```text
DEPENDS="gcc-cross-aarch64 virtual/compilerlibs virtual/libc kern-tools-native virtual/crypt update-rc.d initscripts virtual/update-alternatives"
```

`DEPENDS`는 **Build-time Dependencies(빌드 시 의존성)**다. 8개 항목이 있다.

| `DEPENDS` 값 | 이번 그래프와 연결한 후보 / 확인 상황 |
|---|---|
| `gcc-cross-aarch64` | 그래프에 동일 이름 존재 |
| `virtual/compilerlibs` | 그래프에 `gcc-runtime` 존재 |
| `virtual/libc` | 그래프에 `glibc` 존재 |
| `kern-tools-native` | 그래프에 동일 이름 존재 |
| `virtual/crypt` | 그래프에 `libxcrypt` 존재 |
| `update-rc.d` | 그래프에 동일 이름 존재 |
| `initscripts` | 그래프에 동일 이름 존재 |
| `virtual/update-alternatives` | 그래프에 `opkg-utils` 존재하지만 **직접적인 Provider 대응은 별도 검증 필요** |

위 그래프의 `pseudo-native`, `busybox.do_fetch`처럼 직접 `DEPENDS` 문자열에 없는 항목도 있다. **Task 그래프는 `DEPENDS` 외에도 Class·Task 수준의 의존성을 반영하기 때문**이다.

#### DEPENDS와 RDEPENDS 비교

| 구분 | `DEPENDS` | `RDEPENDS:${PN}` |
|---|---|---|
| 풀네임 | Build-time Dependencies | Runtime Dependencies |
| 언제 필요? | 프로그램을 만드는 중 | 완성된 패키지를 설치·실행할 때 |
| 의존 대상 | Recipe/Provider | 런타임 패키지 |
| 예시 | 크로스 컴파일러, 개발용 라이브러리 | init 프로그램, 공유 라이브러리 등 |

**주의:** `packagegroup-core-boot`의 `RDEPENDS`와 `busybox` Recipe의 `DEPENDS`는 **서로 다른 Recipe의 변수**다. 의존성 비교를 위해 사용했지만 동일한 설정 파일을 읽은 것은 아니다.

---

## 8. Image 생성 Task 및 최종 이미지 설정

### 8.1 `core-image-minimal` Task 목록

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake -c listtasks core-image-minimal`
- **관찰한 주요 출력:**

```text
BB_VERSION           = "2.18.0"
BUILD_SYS            = "x86_64-linux"
NATIVELSBSTRING      = "universal"
TARGET_SYS           = "aarch64-poky-linux"
MACHINE              = "raspberrypi4-64"
DISTRO               = "poky"
DISTRO_VERSION       = "6.0.4"

...
do_rootfs                             Creates the root filesystem (file and directory structure) for an image
do_image
do_image_complete
do_image_ext3
do_image_tar
do_image_wic
do_rootfs_wicenv
...
NOTE: Tasks Summary: Attempted 1 tasks of which 0 didn't need to be rerun and all succeeded.
```

- `do_rootfs`: 선택된 패키지를 설치해 RootFS 구성.
- `do_image`: 이미지 생성 준비 작업.
- `do_image_ext3`: ext3 파일시스템 이미지 생성.
- `do_image_tar`: tar 아카이브 생성.
- `do_image_wic`: Wic 디스크 이미지 생성.
- `do_image_complete`: 이미지 생성 후 마무리 단계.
- `do_rootfs_wicenv`: Wic 관련 환경 설정 작업.

**중요:** `listtasks`에서 출력된 Task는 **등록된 작업 목록**이며, 이 명령으로 RootFS나 이미지가 실제 생성된 것은 아니다. BusyBox Task 조회 때 `NATIVELSBSTRING`은 `ubuntu-26.04`, 이번에는 `universal`로 표시됐다. 값 변화는 관찰했으나 원인을 별도로 실험해 확정하지 않았다.

### 8.2 이미지 형식·패키지·파티션 설정의 최종값

- **실행 위치:** `BUILD_DIR`
- **실행 명령:**

```bash
bitbake -e core-image-minimal | \
  grep -E '^(IMAGE_FSTYPES|IMAGE_INSTALL|WKS_FILE)='
```

- **관찰 출력:**

```text
IMAGE_FSTYPES="tar.bz2 ext3 wic.bz2 wic.bmap"
IMAGE_INSTALL="packagegroup-core-boot "
WKS_FILE="sdimage-raspberrypi.wks"
```

| 형식 | 뜻 |
|---|---|
| `tar.bz2` | RootFS 파일들을 담은 bzip2 압축 tar 아카이브 |
| `ext3` | ext3 파일시스템 이미지 |
| `wic.bz2` | Wic 디스크 이미지 압축본 |
| `wic.bmap` | 디스크 이미지의 유효 블록을 표시하는 블록 맵 |

- 원본 `core-image-minimal.bb`의 `${CORE_IMAGE_EXTRA_INSTALL}`이 최종 `IMAGE_INSTALL` 출력에서 빈 문자열로 확장된 것을 확인했다.
- 원본 `rpi-base.inc`의 `IMAGE_FSTYPES`, `WKS_FILE` 기본값도 최종 출력과 일치했다.
- 이 단계는 Image Task 및 설정 조회이며, **이미지 생성 Task를 실행한 결과는 아니다.** 이미지 빌드 결과는 [별도 기록](03-arm64-image-build.md)에 정리했다.

### 8.3 발생한 Bash 오류와 원인

- **실행 위치:** `BUILD_DIR`
- **잘못 입력한 명령:** `IMAGE_FSTYPES ?= "tar.bz2 ext3 wic.bz2 wic.bmap"`
- **관찰 출력:** `IMAGE_FSTYPES: command not found`
- **원인:** `?=`는 BitBake 설정 문법이지 Bash 명령어가 아니다.
- **영향:** Bash가 실행 파일을 찾다 실패한 것으로, 이 명령 자체가 Yocto 설정 파일을 수정하지는 않았다.

---

## 9. Yocto 6.0 Configuration Fragment

### 9.1 활성 Fragment 목록 조회

- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `bitbake-config-build list-fragments`
- **관찰 출력 중 핵심:**

```text
Available built-in fragments:
machine/...     Sets MACHINE = ...
distro/...      Sets DISTRO = ...

Enabled built-in fragments:
distro/poky     Sets DISTRO = "poky"
machine/raspberrypi4-64 Sets MACHINE = "raspberrypi4-64"

Unused fragments:
core/yocto/root-login-with-empty-password
core/yocto/sbom-cve-check
core/yocto/sstate-mirror-cdn
core/yocto-autobuilder/autobuilder-resource-constraints
core/yocto-autobuilder/autobuilder
core/yocto-autobuilder/multilib-mips64-n32
core/yocto-autobuilder/multilib-x86-lib32
core/yocto-autobuilder/multilib-x86-lib64
```

- Fragment: 독립적으로 선택할 수 있는 설정 조각.
- `Enabled`: 현재 적용되는 Fragment.
- `Unused`: 사용할 수는 있지만 현재 활성화되지 않은 Fragment.
- `root-login-with-empty-password`: 비밀번호 없는 root 로그인 허용. 보안상 위험할 수 있으므로 **이번 실습에서 활성화하지 않았다.**
- `CVE`: Common Vulnerabilities and Exposures / 공개된 취약점 식별 체계.

### 9.2 `toolcfg.conf` 파일 검증

- **파일 절대 경로:** `/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/conf/toolcfg.conf`
- **실행 위치:** `BUILD_DIR`
- **실행 명령:** `cat conf/toolcfg.conf`
- **관찰 원문:**

```bitbake
# Automated config file controlled by tools
#
# Run 'bitbake-config-build enable-fragment <fragment-name>' to enable additional fragments
# or replace built-in ones (e.g. machine/<name> or distro/<name> to change MACHINE or DISTRO).

OE_FRAGMENTS += "distro/poky machine/raspberrypi4-64"
```

`OE_FRAGMENTS`의 두 값이 앞서 `list-fragments` 결과와 일치한다. 이 파일은 도구가 관리하므로 직접 편집하지 않는 것을 원칙으로 배웠다.

### 9.3 설정 파일 역할 비교

| 파일 경로 | 역할 | 이 실습에서 원본 내용 확인? |
|---|---|---|
| `BUILD_DIR/conf/bblayers.conf` | 활성 Layer 경로 | **예** (`cat`) |
| `BUILD_DIR/conf/toolcfg.conf` | 활성 Configuration Fragment | **예** (`cat`) |
| `BUILD_DIR/conf/local.conf` | 사용자별 빌드 환경·병렬도 등 | **아니오** (환경 구성 기록의 값 참조) |
| `LAYERS_DIR/meta-yocto/meta-poky/conf/distro/poky.conf` | 배포판 정책 | **예** (`cat`) |
| `LAYERS_DIR/meta-raspberrypi/conf/machine/raspberrypi4-64.conf` | 대상 머신 설정 | **예** (`cat`) |

---

## 10. 중요한 BitBake 문법 정리

| 문법 | 뜻 | 실제 발견한 파일 예시 |
|---|---|---|
| `=` | 변수 할당(일반적으로 사용 시 확장) | `poky.conf`: `DISTRO = "poky"` |
| `?=` | 아직 정의되지 않았으면 기본값 지정 | `rpi-base.inc`: `IMAGE_FSTYPES ?= ...` |
| `??=` | 약한 기본값 지정 | `rpi-default-providers.inc`: 커널 Provider |
| `+=` | 공백을 넣어 값 추가 | `raspberrypi4-64.conf`: `MACHINE_FEATURES += "pci"` |
| `.=` | 공백 없이 뒤에 연결 | `layer.conf`: `BBPATH .= ...` |
| `=.` | 공백 없이 앞에 연결 | `raspberrypi4-64.conf`: `MACHINEOVERRIDES =. ...` |
| `:append` | 변수에 문자열 추가하는 Override 방식 | `core-image-minimal.bb`: RootFS 추가 공간 |
| `:remove` | 지정 값을 제거하는 Override 방식 | `layer.conf`: 테스트 Suite 조정 |
| `${VAR}` | 변수 참조 및 확장 | `IMAGE_INSTALL` 안의 `${CORE_IMAGE_EXTRA_INSTALL}` |
| `${@...}` | Python 표현식에 의한 값 계산 | `bb.utils.contains(...)` |
| `inherit` | `.bbclass` 기능 적용 | `core-image-minimal.bb`: `inherit core-image` |
| `require` | 반드시 있어야 하는 파일 포함 | 머신 설정의 `tune-cortexa72.inc` |
| `include` | 파일이 있으면 포함 | 머신 설정의 `rpi-base.inc` |

**기억할 구분:** “설정 파일에서 읽은 문자열”과 “`bitbake -e`가 계산한 최종값”은 다를 수 있다. 이 때문에 Provider, `MACHINE_FEATURES`, `DEPENDS`, `RDEPENDS`, 이미지 설정을 `bitbake -e`로 따로 검증했다.

---

## 11. 실습 명령 및 출력 추적 색인

아래 **모든 명령의 실행 위치**는 `BUILD_DIR`이다. `../layers/...`도 모두 이 위치를 기준으로 한 상대 경로다. 코드 일부는 길이 때문에 핵심 변수만 표시했다. 상세 출력과 경로는 해당 절을 참조한다.

| 순서 | 실행 명령 | 출력/검증한 대상 | 이 문서 위치 |
|---:|---|---|---|
| 1 | `bitbake -p` | 992 Recipe 파싱, 0 오류 | §2.1 |
| 2 | `command -v bitbake` | BitBake 바이너리 절대 경로 | §2.2 |
| 3 | `bitbake-layers show-layers` | Layer 4개 및 Priority | §3.1 |
| 4 | `cat conf/bblayers.conf` | BBLAYERS 경로 4개 | §3.2 |
| 5 | `cat ../layers/meta-raspberrypi/conf/layer.conf` | BBFILES·Layer Priority | §3.3 |
| 6 | `ls ../layers/meta-raspberrypi/recipes*/*/*.bb \| head -n 10` | `.bb` 파일 경로 10개 | §3.4 |
| 7 | `ls -l ../layers/meta-yocto/meta-poky/conf/distro/poky.conf ../layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf` | 두 설정 파일의 실제 경로·크기 | §4.1 |
| 8 | `cat ../layers/meta-yocto/meta-poky/conf/distro/poky.conf` | Poky 배포판 설정 | §4.2 |
| 9 | `cat ../layers/meta-raspberrypi/conf/machine/raspberrypi4-64.conf` | Pi 4 머신 설정 | §4.3 |
| 10 | `sed -n '1,100p' ../layers/meta-raspberrypi/conf/machine/include/rpi-base.inc` | 공통 이미지·DT Overlay 설정 | §4.5 |
| 11 | `cat ../layers/meta-raspberrypi/conf/machine/include/rpi-default-providers.inc` | Provider 조건식 | §5.1 |
| 12 | `bitbake -e \| grep -E '^(MACHINE_FEATURES\|PREFERRED_PROVIDER_virtual/egl)='` | vc4graphics 포함, Mesa 선호 | §5.2 |
| 13 | `bitbake -e \| grep '^PREFERRED_PROVIDER_virtual/kernel='` | linux-raspberrypi 선택 | §5.3 |
| 14 | `cat ../layers/openembedded-core/meta/recipes-core/images/core-image-minimal.bb` | Image Recipe 내용 | §6.1 |
| 15 | `cat ../layers/openembedded-core/meta/recipes-core/packagegroups/packagegroup-core-boot.bb` | 부팅 패키지 그룹 내용 | §6.2 |
| 16 | `bitbake -e packagegroup-core-boot \| grep -E '^R(DEPENDS\|RECOMMENDS):packagegroup-core-boot='` | 필수·권장 패키지 최종값 | §6.3 |
| 17 | `bitbake -e packagegroup-core-boot \| grep -E '^VIRTUAL-RUNTIME_(base-utils\|login_manager\|init_manager\|dev_manager)='` | busybox/sysvinit/udev | §6.4 |
| 18 | `bitbake -c listtasks busybox` | BusyBox Task 목록 | §7.1 |
| 19 | `bitbake -g busybox` | `pn-buildlist`, `task-depends.dot` 생성 | §7.2 |
| 20 | `grep -F '"busybox.do_compile" ->' task-depends.dot` | 컴파일 선행 Task | §7.3 |
| 21 | `grep -F '"busybox.do_configure" ->' task-depends.dot \| head -n 15` | 설정 선행 Task | §7.4 |
| 22 | `grep -F '"busybox.do_prepare_recipe_sysroot" ->' task-depends.dot \| head -n 15` | 다른 Recipe의 sysroot Task | §7.5 |
| 23 | `bitbake -e busybox \| grep '^DEPENDS='` | 8개 빌드 의존성 | §7.6 |
| 24 | `bitbake -c listtasks core-image-minimal` | RootFS·Image Task 목록 | §8.1 |
| 25 | `bitbake -e core-image-minimal \| grep -E '^(IMAGE_FSTYPES\|IMAGE_INSTALL\|WKS_FILE)='` | 이미지 형식 및 패키지 설정 | §8.2 |
| 26 | `IMAGE_FSTYPES ?= "tar.bz2 ext3 wic.bz2 wic.bmap"` | Bash 문법 오류 | §8.3 |
| 27 | `bitbake-config-build list-fragments` | 활성 Fragment 두 개 | §9.1 |
| 28 | `cat conf/toolcfg.conf` | OE_FRAGMENTS 설정 | §9.2 |

---

## 12. 실습 결과 및 검증 범위

### 12.1 확인한 작업

- [x] BitBake 파싱과 실제 빌드의 차이 검증 (`992 .bb`, 오류 0)
- [x] Layer 4개 확인과 `bblayers.conf` ↔ `layer.conf` 연결
- [x] `.bb` 탐색 패턴으로 Raspberry Pi Recipe 파일 경로 확인
- [x] OpenEmbedded-Core·Poky·BSP의 역할 구별
- [x] `DISTRO`와 `MACHINE`의 설정 파일 및 내용 확인
- [x] `require` / `include`, BitBake 변수 연산자 학습
- [x] `MACHINE_FEATURES`의 `vc4graphics`와 EGL Provider 최종값 확인
- [x] Kernel Provider 최종값 `linux-raspberrypi` 확인
- [x] `core-image-minimal.bb`와 `packagegroup-core-boot.bb` 내용 확인
- [x] `RDEPENDS`, `RRECOMMENDS`, `VIRTUAL-RUNTIME_*` 최종값 확인
- [x] BusyBox Task 열거, 의존성 그래프 생성 및 관계 추적
- [x] `DEPENDS`와 Task 의존성 그래프 비교
- [x] Image Task 및 `IMAGE_FSTYPES`·`IMAGE_INSTALL`·`WKS_FILE` 확인
- [x] 활성 Configuration Fragment, `toolcfg.conf` 값 검증

### 12.2 실습 중 파일 변경 여부

- **이 과정에서 의도적으로 수정한 Yocto 설정 파일:** 없음.
- **BitBake 실행에 따라 생성·변경될 수 있는 파일:** Recipe 파싱 캐시, BitBake 서버 로그, `pn-buildlist`, `task-depends.dot`, 보조 툴 다운로드 자료.
- **새로 생성된 것으로 출력으로 확인된 파일:** `BUILD_DIR/pn-buildlist`, `BUILD_DIR/task-depends.dot`.
- **전체 Linux 이미지:** 이 조회 중심 실습에서는 생성하지 않았다. 실제 빌드 검증은 [별도 기록](03-arm64-image-build.md)에 있다.

### 12.3 분석 범위와 실장비 검증의 연결

이 장에서 확보한 근거는 **집 환경의 Parse·메타데이터 조회 결과**이다. `local.conf` 전문, `rpi-base.inc` 101줄 이후, 설치된 RootFS 패키지 목록과 일부 Provider 대응은 이 조회 과정에서 확인되지 않았다.

이후 센터 환경의 실제 이미지 빌드 결과는 [Chapter 3](03-arm64-image-build.md), Raspberry Pi 4B에서의 커널·RootFS·네트워크·외부 모듈 동작은 [Chapter 5](05-raspberrypi-boot.md)에 기록했다.

---

## 13. 이번 챕터 약어·용어 빠른 참조

| 표기 | 전체 명칭 / 한국어 뜻 | 핵심 역할 |
|---|---|---|
| ARM64 / AArch64 | ARM 64-bit Architecture / ARM 64비트 아키텍처 | Raspberry Pi 4 타깃 실행 환경 |
| BSP | Board Support Package / 보드 지원 패키지 | 하드웨어별 부팅·커널·장치 설정 제공 |
| CWD | Current Working Directory / 현재 작업 디렉터리 | 명령의 상대 경로 해석 기준 |
| DTB | Device Tree Blob / 장치 트리 바이너리 | 커널에 보드 하드웨어 정보 전달 |
| EGL | Embedded-System Graphics Library / 임베디드 그래픽 인터페이스 | 그래픽 렌더링 환경 구성에 사용 |
| EFI | Extensible Firmware Interface / 확장 펌웨어 인터페이스 | 부팅 펌웨어 인터페이스 규격 |
| GCC | GNU Compiler Collection / GNU 컴파일러 모음 | 호스트에서 ARM64 코드를 생성하는 크로스 도구 포함 |
| GPU | Graphics Processing Unit / 그래픽 처리 장치 | 그래픽 하드웨어 연산 |
| OE-Core | OpenEmbedded-Core / OpenEmbedded 핵심 구성 | 공통 Recipe·Class·설정 |
| PN | Recipe Name 변수 / 레시피 이름 변수 | Recipe와 기본 패키지 이름 식별에 사용 |
| RootFS | Root File System / 루트 파일시스템 | 타깃 장치의 `/` 이하 파일 계층 |
| RPM | RPM Package Manager / RPM 패키지 관리자·형식 | `.rpm` 패키징 |
| SBOM | Software Bill of Materials / 소프트웨어 구성 요소 명세서 | 패키지·구성 요소 추적 |
| SDK | Software Development Kit / 소프트웨어 개발 키트 | 타깃 개발 도구 묶음 |
| WKS | Wic Kickstart / Wic 파티션 정의 파일 형식 | SD 이미지의 파티션 구성 기술 |
| Wic | Yocto 디스크 이미지 생성 도구 이름 | `.wic` 디스크 이미지 제작 |
| UART | Universal Asynchronous Receiver/Transmitter / 범용 비동기 송수신기 | 시리얼 통신·로그 확인 |

## 관련 구현·검증

- [Chapter 6 — Custom Layer·모듈·앱 Recipe](06-custom-layer.md): 이 장에서 분석한 Layer·Task·sysroot 구조를 실제 사용자 모듈·앱 빌드에 적용한 결과
- [Chapter 4 — RootFS·Wic 분석](04-rootfs-analysis.md): Image 설정과 배포·실행 산출물의 연결
