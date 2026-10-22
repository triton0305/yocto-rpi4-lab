# Chapter 1 — Yocto 개발 환경 구성

## 1. 목표와 검증 범위

WSL2 Ubuntu(x86-64)에서 Yocto Project 6.0.4(wrynose) 환경을 구성하고 Raspberry Pi 4B(ARM64)용 이미지 빌드 준비를 완료한다.

이 문서의 **검증 완료** 표기는 기존 실습 기록에 근거합니다. 이미지 생성과 Raspberry Pi 실부팅은 아직 수행하지 않았습니다. 별도 표시한 **재현·점검 명령**은 이번 문서 정비에서 WSL에서 다시 실행한 결과가 아닙니다.

## 2. 작업 디렉터리

기존 실습에서 사용한 로컬 경로는 다음과 같이 기록되어 있습니다.

```text
~/study/rootfs/yocto/
├── bitbake/                       # 최초 bitbake-setup 실행을 위해 clone
└── bitbake-builds/
    └── poky-wrynose/
        ├── build/                 # BitBake Build Directory
        └── layers/                # Setup에서 관리하는 Layer 및 Source
```

`bitbake-setup init`의 실제 설정 이름과 위치는 초기화 선택에 따라 달라질 수 있습니다. 위 경로는 이 프로젝트에서 기록한 경로이며 GitHub에 실제 디렉터리 전체를 커밋한 것은 아닙니다.

## 3. BitBake 설치 및 Setup 초기화 (수행 기록)

```bash
cd ~/study/rootfs/yocto
git clone https://git.openembedded.org/bitbake
./bitbake/bin/bitbake-setup init
```

- `git clone`: `bitbake-setup`이 포함된 BitBake 소스를 가져옵니다.
- `bitbake-setup init`: Configuration Template과 Target 선택에 따라 Yocto Setup 및 Build Directory를 생성합니다.

기존 실습에서 기록한 선택 항목:

| 항목 | 선택 |
|---|---|
| Configuration | `poky-wrynose` |
| BitBake Configuration | `poky` |
| 초기 Target Machine | `qemuarm64` |
| Distribution | `poky` |

초기 Target은 이후 Raspberry Pi 4B로 변경했습니다.

### 새로운 Shell에서 Build Environment 준비 (공식 절차 보완)

Yocto 6.0 문서에서는 `bitbake-setup`으로 생성한 Setup의 `build/init-build-env`를 현재 Shell에서 `source`하도록 안내합니다.

```bash
cd ~/study/rootfs/yocto
source bitbake-builds/poky-wrynose/build/init-build-env
```

이 스크립트는 현재 Shell에 빌드 환경을 적용하고 Build Directory로 이동하도록 준비합니다. 이후의 `../layers`는 **Build Directory 기준 상대 경로**입니다.

**기록 구분:** 기존 Chapter 1에는 이 `source` 명령의 실행 로그가 남아 있지 않았습니다. 위 명령은 공식 문서 및 기존 경로에 근거한 재현 절차이며, 이번 정비에서 직접 재실행했다고 주장하지 않습니다.

## 4. Locale 오류 해결 (수행·검증 기록)

BitBake 서버 시작 시 다음 메시지가 나타났습니다.

```text
Please make sure locale 'en_US.UTF-8' is available on your system
```

기존 실습에서 Ubuntu의 Locale을 생성하고 기본 Locale 설정을 변경했습니다.

```bash
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
```

- `locale-gen`: 지정한 Locale 데이터를 생성합니다.
- `update-locale`: 시스템 기본 Locale 설정을 갱신합니다.

**검증 기록:** `locale -a`에서 `en_US.utf8` 항목을 확인했습니다.

## 5. Raspberry Pi BSP Layer 등록 (수행·검증 기록)

Build Environment를 준비한 뒤, Build Directory를 기준으로 다음 명령을 사용한 것으로 기록되어 있습니다.

```bash
git clone -b wrynose https://git.yoctoproject.org/meta-raspberrypi ../layers/meta-raspberrypi
bitbake-layers add-layer ../layers/meta-raspberrypi
bitbake-layers show-layers
```

- `git clone -b wrynose`: Raspberry Pi 관련 BSP Layer의 `wrynose` 브랜치를 가져옵니다.
- `bitbake-layers add-layer`: 해당 Layer를 빌드의 Layer 구성에 등록합니다.
- `bitbake-layers show-layers`: BitBake가 인식한 Layer와 Priority를 조회합니다.

**검증 기록:** 출력에서 `raspberrypi` Layer 및 Priority `9`를 확인했습니다.

## 6. Raspberry Pi 4B Machine 적용 (수행·검증 기록)

초기 `qemuarm64`에서 `raspberrypi4-64`로 Target Machine을 변경했습니다.

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

`machine/raspberrypi4-64` Fragment를 활성화하여 `MACHINE` 값을 구성합니다. Yocto 6.0의 `bitbake-config-build`는 활성화한 Fragment를 `build/conf/toolcfg.conf`의 `OE_FRAGMENTS`에 반영합니다. 이는 `local.conf`에 `MACHINE` 값을 직접 입력하는 방식과 구별됩니다.

기존 `bitbake -e` 환경 변수 확인 결과:

```text
DISTRO="poky"
DISTRO_VERSION="6.0.4"
MACHINE="raspberrypi4-64"
MACHINE_ARCH="raspberrypi4_64"
```

## 7. 빌드 병렬도 제한 (수행·검증 기록)

기존 기록상 WSL2 메모리 할당량은 15GiB입니다. 자원 사용을 제한하기 위해 `build/conf/local.conf`에 다음 값을 설정했습니다.

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

- `BB_NUMBER_THREADS`: BitBake가 동시에 실행할 최대 Task 수를 제한합니다.
- `PARALLEL_MAKE`: `do_compile` 등의 빌드 도구에 전달하는 병렬 컴파일 옵션입니다. 실제 사용 방식은 Recipe와 빌드 도구에 따라 달라집니다.

**검증 기록:** `bitbake -e`에서 두 설정이 적용된 것을 확인했습니다. 세부 설정 출처와 확인 명령은 [빌드 설정](../configs/build-config.md)을 참조합니다.

## 8. 결과와 미검증 범위

| 항목 | 상태 | 근거 |
|---|---|---|
| BitBake Setup 초기화 | 완료 | 기존 실습 기록 |
| Locale 문제 해결 | 완료 | `locale -a` 확인 기록 |
| Raspberry Pi BSP 등록 | 완료 | `show-layers` 및 Priority 9 확인 기록 |
| Machine 및 Distribution 설정 | 완료 | `bitbake -e` 값 확인 기록 |
| 병렬도 제한 | 완료 | `bitbake -e` 확인 기록 |
| `init-build-env` 명령 재실행 | 이번 정비에서 미검증 | 공식 절차 보강 |
| `core-image-minimal` 이미지 빌드 | 미진행 | 빌드 로그 없음 |
| Raspberry Pi 4B 부팅 | 미진행 | 실장비 검증 기록 없음 |

**Chapter 1 환경 구성 완료(기존 실습 기준).** 이후 Chapter에서는 이미지 빌드, 산출물 분석, 실제 부팅을 각각 별도로 검증합니다.

## 참고 문서

- [Yocto Project 6.0 — Setting Up to Use the Yocto Project](https://docs.yoctoproject.org/6.0/dev-manual/start.html)
- [Yocto Project 6.0 — Quick Build](https://docs.yoctoproject.org/6.0/brief-yoctoprojectqs/index.html)
- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
