# Chapter 1 — Yocto 개발 환경 구성

## 1. 목표와 검증 범위

WSL2 Ubuntu(x86-64)에서 Yocto Project 6.0.4(wrynose) 환경을 구성하고 Raspberry Pi 4B(ARM64)용 이미지 빌드를 준비한다. **센터의 기존 환경 구성 기록**과 **집 노트북의 후속 Parse 검증 기록**을 구분한다.

이 문서의 **검증 완료** 표기는 기존 실습 기록에 근거합니다. 센터에서 확보된 초기화 오류 원문과 확인 결과는 [센터 실행 근거](logs/01-center-setup.md)에, 집에서 제공된 터미널 출력은 [집 실행 로그](logs/01-home-setup.md)에 분리했습니다. 이미지 생성과 Raspberry Pi 실부팅은 아직 수행하지 않았습니다. 별도 표시한 **재현·점검 명령**은 이번 문서 정비에서 WSL에서 다시 실행한 결과가 아닙니다.

## 2. 작업 디렉터리

센터 실습에서 사용한 경로는 다음과 같습니다. 집 노트북에서도 `pwd`, `command -v bitbake`와 Git 조회 결과로 해당 `poky-wrynose/build`·`layers` 경로 및 최상위 BitBake Clone 경로를 확인했습니다([집 실행 로그](logs/01-home-setup.md)).

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

**기록 구분:** [센터 초기화 오류 원문](logs/01-center-setup.md#1-bitbake-초기화-중-locale-오류--원문-발췌)에서는 `bitbake-setup init`의 내부 `init-build-env` 호출을 확인했지만 센터의 별도 수동 `source` 로그는 없습니다. **집 노트북은 `source` 실행 뒤 `pwd`와 `command -v bitbake`를 확인한 원문 출력이 있습니다**([집 실행 로그](logs/01-home-setup.md#7-build-environment-진입-및-초기-layer--실행-로그)). 이번 문서 수정 과정에서 WSL을 직접 재실행하지는 않았습니다.

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

**검증 기록:** `locale -a`에서 `en_US.utf8` 항목을 확인했습니다. 실제 실패 시점의 반복 서버 오류와 복구 후 확인값은 [센터 실행 근거](logs/01-center-setup.md)에 증거 유형을 구분하여 정리했습니다.

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

센터 환경의 기존 기록상 WSL2 메모리 할당량은 15GiB입니다. 자원 사용을 제한하기 위해 센터의 `build/conf/local.conf`에 다음 값을 설정했습니다.

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

**Chapter 1 환경 구성 완료(기존 센터 기록 및 아래 집 노트북 검증 기준).** 센터의 원문 로그 및 검증 결과의 차이는 [센터 실행 근거](logs/01-center-setup.md)에서 확인할 수 있습니다. 이후 Chapter에서는 이미지 빌드, 산출물 분석, 실제 부팅을 각각 별도로 검증합니다.

## 9. 집 노트북 환경 구성 및 Recipe Parse 검증

이 절은 2026-10-22~23 집 WSL2에서 수행한 환경 구성과 Parse 검증의 **요약**입니다. 전체 명령어·출력 및 중복 Setup 정리 과정은 [집 Chapter 1 실행 로그](logs/01-home-setup.md)를 참조합니다. 수치는 사용자가 제공한 터미널 기록에 근거하며, GitHub 문서 수정 중 명령을 직접 재실행하지 않았습니다.

| 항목 | 확인된 집 노트북 결과 |
|---|---|
| Host OS | WSL2 Ubuntu 26.04.1 LTS |
| 논리 CPU / RAM / Swap | 8 / 7.6GiB / 2.0GiB |
| 당시 Windows C: 여유 공간 | 70G (실제 물리 여유 공간은 변동 가능) |
| Yocto / DISTRO / MACHINE | 6.0.4 (wrynose) / `poky` / `raspberrypi4-64` |
| BSP Layer | `raspberrypi` Priority 9 포함 총 4개 |
| 병렬도 | `BB_NUMBER_THREADS=2`, `PARALLEL_MAKE="-j 2"` |
| 실행용 BitBake | `layers/bitbake/bin/bitbake` |
| BitBake Recipe Parse | 992 `.bb`, 2013 targets, 73 skipped, 0 masked, 0 errors, Exit 0 |
| WSL2 경고 | VHDX 저장 공간 최적화 권고 1건 |
| 이미지 빌드 / Raspberry Pi 부팅 | **미진행 / 미진행** |

집에서 실제 실행했다고 제공된 명령:

```bash
bitbake -p
echo $?
```

발췌 결과:

```text
Parsing of 992 .bb files complete (0 cached, 992 parsed). 2013 targets, 73 skipped, 0 masked, 0 errors.
Summary: There was 1 WARNING message.
```

종료 코드 `0`을 확인했습니다. `-p`는 Recipe 메타데이터의 Parse Only 동작으로, **컴파일·이미지 생성·실부팅 성공을 의미하지 않습니다.** WSL2 관련 경고는 파싱 오류와 구분하고, 전체 빌드 전에 Host 저장 공간을 확인합니다.

집·센터의 설정 차이는 [빌드 설정](../configs/build-config.md), 각 Source의 Git SHA는 [소스 리비전](../configs/source-revisions.md)을 참조합니다. Chapter 2 첫 조회 예정 명령은 `bitbake-layers show-recipes busybox`이며 여기서는 수행 완료로 처리하지 않습니다.

## 참고 문서

- [Yocto Project 6.0 — Setting Up to Use the Yocto Project](https://docs.yoctoproject.org/6.0/dev-manual/start.html)
- [Yocto Project 6.0 — Quick Build](https://docs.yoctoproject.org/6.0/brief-yoctoprojectqs/index.html)
- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
- [BitBake 2.16 — Command options, `-p` / `--parse-only`](https://docs.yoctoproject.org/bitbake/2.16/bitbake-user-manual/bitbake-user-manual-intro.html)
