# Yocto 빌드 설정

이 문서는 환경 구성 명령을 중복 나열하지 않고, **설정의 출처·의미·적용값·점검 방법**을 정리합니다. 실제 진행 순서 및 과거 검증 기록은 [Chapter 1](../docs/01-environment.md)을 참조합니다.

## 1. 센터·집 설정 비교

두 Host의 `local.conf`는 서로 다른 자원 조건에 맞춰 설정했다. 아래 값은 센터와 집에서 확인한 기록을 기준으로 한다.

| 항목 | 센터 | 집 |
|---|---|---|
| Host | WSL2 Ubuntu 22.04 (Chapter 1·5 기록 기준) | WSL2 Ubuntu 26.04.1 LTS (x86-64) |
| WSL2 RAM | 15GiB | 7.6GiB |
| 논리 CPU | 24개(기존 기록) | **8개** (`nproc` 출력) |
| Yocto | 6.0.4 (wrynose) | 6.0.4 (wrynose) |
| `DISTRO` | `poky` | `poky` |
| `MACHINE` | `raspberrypi4-64` | `raspberrypi4-64` |
| BSP Layer | `meta-raspberrypi` | `meta-raspberrypi` |
| `BB_NUMBER_THREADS` | `4` | `2` |
| `PARALLEL_MAKE` | `-j 4` | `-j 2` |
| `bitbake -p` | 별도 기록 없음 | 성공: 992 `.bb`, 0 errors, Exit 0 |

설정 출처는 초기 `bitbake-setup`에서 선택한 `poky`, 활성화한 `machine/raspberrypi4-64` Fragment, BSP Layer 등록, 각 Host의 `build/conf/local.conf`입니다. 집의 `bitbake -e` 적용 결과는 [집 실행 로그](../docs/logs/01-home-setup.md)에 보존되어 있다.

## 2. Target Machine과 Configuration Fragment

초기 `qemuarm64` 구성에서 Raspberry Pi 4B용으로 변경할 때 다음 명령을 사용했습니다.

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

- `enable-fragment`: Fragment를 활성화하여 해당 설정을 BitBake 환경에 적용합니다.
- Yocto 6.0에서는 활성화한 Fragment 이름을 `build/conf/toolcfg.conf`의 `OE_FRAGMENTS`에 자동 반영합니다.
- `DISTRO=poky`는 기존 Setup 초기 선택 기록입니다. 이후 [Chapter 2](../docs/02-bitbake-layer-recipe.md#9-yocto-60-configuration-fragment)에서 사용자가 `cat conf/toolcfg.conf` 출력으로 `OE_FRAGMENTS += "distro/poky machine/raspberrypi4-64"`를 확인했습니다. 설정값은 기록된 `cat conf/toolcfg.conf` 출력에 근거한다.

설정 확인용 명령:

```bash
bitbake-config-build list-fragments
bitbake -e | grep -E '^(MACHINE|DISTRO)='
```

`list-fragments`는 사용 가능·활성화 상태의 Fragment를 살펴보고, `bitbake -e`는 최종 BitBake 변수 값을 조회합니다.

## 3. Host별 병렬 빌드 제한

**센터의 `build/conf/local.conf` (기존 수행 기록)**

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

**집의 `build/conf/local.conf` (사용자 제공 설정·적용값 검증 기록)**

```conf
BB_NUMBER_THREADS = "2"
PARALLEL_MAKE = "-j 2"
```

집에서는 보고된 RAM 7.6GiB를 고려해 센터보다 병렬도를 낮췄습니다. 이는 자원 사용을 줄이기 위한 설정이며, 전체 이미지 빌드 성공 여부나 필요 자원 충족을 증명하지 않습니다.

| 변수 | 역할 |
|---|---|
| `BB_NUMBER_THREADS` | 동시 BitBake Task 수의 상한 |
| `PARALLEL_MAKE` | 컴파일 Task에서 사용하는 빌드 도구의 병렬 옵션. 일반적으로 `-j N` 형태 |

두 설정은 다른 계층의 병렬성을 제어합니다. `BB_NUMBER_THREADS`만 줄여도 각 Task 내부의 병렬 컴파일은 계속 실행될 수 있으므로, 자원 제한 목적에서 두 값을 함께 조정했습니다.

## 4. 설정 확인

Build Environment를 활성화한 Shell에서 실행할 수 있는 명령입니다.

```bash
bitbake -e | grep -E '^(MACHINE|DISTRO|BB_NUMBER_THREADS|PARALLEL_MAKE)='
bitbake-layers show-layers
```

- 첫 번째 명령: BitBake의 실제 적용 변수 확인
- 두 번째 명령: 현재 등록된 Layer와 Priority 확인

센터 기존 실습 기록에서는 `MACHINE=raspberrypi4-64`, `DISTRO=poky`, 센터 병렬도 값 적용 및 `raspberrypi` Layer Priority 9를 확인했습니다. 집에서는 `bitbake -e`로 `MACHINE`, `DISTRO`, 병렬도 `2 / -j 2`의 실제 출력이 확보됐고 `bitbake -p` 또한 정상 종료했습니다. 출력 상세는 [집 실행 로그](../docs/logs/01-home-setup.md)에 있습니다. 수치는 해당 환경의 실행 기록에 근거한다.

## 5. 이미지 빌드 및 실장비 검증 현황

- [x] Build Environment 및 BSP Layer 구성 (기존 기록)
- [x] Target Machine·병렬도 설정 확인 (센터의 기존 기록)
- [x] 집 `bitbake -p` Parse 정상 종료 (사용자 제공 결과)
- [x] 센터 환경 `core-image-minimal` 최초 빌드 성공 — [Chapter 3](../docs/03-arm64-image-build.md) (4,025 Tasks 모두 성공)
- [x] Raspberry Pi 4B UART 부팅·root 로그인·Ethernet 검증 — [Chapter 5](../docs/05-raspberrypi-boot.md)
- [x] 외부 커널 모듈 `hello_drv.ko` 빌드·전송·수동 적재·제거 — [실장비 로그](../docs/05-raspberrypi-boot.md), [소스](../examples/hello-drv/README.md)

외부 Source Checkout 버전은 [소스 리비전](source-revisions.md) 문서에서 별도로 관리합니다.

`toolcfg.conf`, `bblayers.conf`, Provider 및 Image 설정의 조회 결과는 [BitBake·Layer·Recipe 분석](../docs/02-bitbake-layer-recipe.md)을 참조한다. 센터의 이미지 빌드와 실장비 검증은 [Chapter 3](../docs/03-arm64-image-build.md)·[Chapter 5](../docs/05-raspberrypi-boot.md)에 기록했다.

## 6. 사용자 Layer와 실행 시스템 연결

센터에서 직접 개발한 모듈·앱의 Yocto 빌드·배포는 구성한 `meta-yocto-lab` Layer에서 진행했다. 커널 빌드는 `raspberrypi4-64`의 `6.18.33-v8`, 앱은 `aarch64-poky-linux` 타깃을 사용했다. 모듈 Recipe·앱 Recipe의 구성과 실제 빌드 출력은 [Chapter 6](../docs/06-custom-layer.md) 및 [검증 로그](../docs/logs/06-module-packaging.md)에 있다.

| 구분 | 확인한 설정·결과 | 근거 |
|---|---|---|
| Kernel / modules | `CONFIG_MODULES=y`, `KERNEL_VERSION="6.18.33-v8"` | [Chapter 5 §10.1](../docs/05-raspberrypi-boot.md#101-모듈-빌드-가능-조건-확인) |
| UART | SD `enable_uart=1`, `console=serial0,115200`; 실행 시 `ttyS0` | [Chapter 5 §5](../docs/05-raspberrypi-boot.md#5-uart-콘솔-설정과-첫-부팅) |
| Init | 메타데이터 `sysvinit`, 부팅 로그 runlevel 5 | [Chapter 2](../docs/02-bitbake-layer-recipe.md#64-가상-런타임-변수의-최종값) · [Chapter 5](../docs/05-raspberrypi-boot.md#82-dhcp-동작-확인) |
| 개발용 로그인 | root 로그인 Fragment 적용 후 증분 빌드·재로그인 | [Chapter 5 §6](../docs/05-raspberrypi-boot.md#6-root-로그인-허용-및-이미지-재빌드) |

UART 옵션은 SD 부팅 파티션에 수동 반영한 설정이다. 8채널 GPIO 전용 이미지의 패키지·Overlay·자동 실행 구성은 [Chapter 7의 통합 설계](../docs/07-gpio-toggle-image.md)에서 별도로 설명한다.

## 참고 문서

- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
- [Yocto Project 6.0 — Variables Glossary](https://docs.yoctoproject.org/6.0/ref-manual/variables.html)
