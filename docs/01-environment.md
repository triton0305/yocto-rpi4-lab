# Chapter 1 — Yocto 개발 환경 구성

## 1. 목표와 검증 범위

WSL2 Ubuntu(x86-64)에서 Yocto Project 6.0.4(wrynose) 환경을 구성하고 Raspberry Pi 4B(ARM64)용 이미지 빌드를 준비한다. **센터의 기존 환경 구성 기록**과 **집 노트북의 후속 Parse 검증 기록**을 구분한다.

이 문서의 **검증 완료** 표기는 기존 실습 기록에 근거합니다. 센터에서 확보된 실제 초기화 오류 원문과 각 단계의 검증 결과는 [센터 실행 근거](logs/01-center-setup.md)에 분리했습니다. 이미지 생성과 Raspberry Pi 실부팅은 아직 수행하지 않았습니다. 별도 표시한 **재현·점검 명령**은 이번 문서 정비에서 WSL에서 다시 실행한 결과가 아닙니다.

## 2. 작업 디렉터리

센터 실습에서 사용한 로컬 경로는 다음과 같이 기록되어 있습니다. 집 노트북은 동일한 경로의 전체 구조를 이번 자료만으로 재확인하지 않았습니다.

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

**기록 구분:** [센터 초기화 오류 원문](logs/01-center-setup.md#1-bitbake-초기화-중-locale-오류--원문-발췌)에는 `bitbake-setup init` 내부에서 `init-build-env`가 호출된 흔적이 있습니다. 그러나 위 `source` 명령을 사용자가 **별도로 수동 실행**했다는 원문 로그는 확보되지 않았습니다. 이 명령은 현재 재현 절차로 제시한 것이며 이번 문서 정비에서 재실행하지 않았습니다.

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

## 9. 집 노트북 환경 구성 및 Recipe Parse 검증 (추가 기록)

아래 수치는 **사용자가 제공한 집 노트북 실습 결과**를 옮긴 것입니다. GitHub 문서 수정 작업에서 WSL에 접속하거나 터미널 원본 로그를 직접 재실행·검증하지 않았습니다.

| 항목 | 집 노트북의 보고된 상태 |
|---|---|
| Host OS | WSL2 Ubuntu 26.04.1 LTS |
| RAM | 7.6GiB |
| Windows C: 여유 공간 | 약 70GB (당시 보고값, 수시로 변동 가능) |
| Yocto | 6.0.4 (wrynose) 초기화 완료 |
| OpenEmbedded-Core / meta-raspberrypi | 구성 완료 |
| DISTRO / MACHINE | `poky` / `raspberrypi4-64` |
| `BB_NUMBER_THREADS` / `PARALLEL_MAKE` | `2` / `-j 2` |
| GitHub 저장소 연결 | 완료(사용자 보고, 당시 HEAD는 미대조) |
| `core-image-minimal` 이미지 빌드 | 미진행 |
| Raspberry Pi 부팅 | 미진행 |

### 9.1 실행 명령 및 역할

```bash
bitbake -p
echo $?
```

- `bitbake -p`(`--parse-only`): 선택된 Build Configuration에서 Recipe 메타데이터를 파싱한 후 실제 빌드 Task를 실행하지 않고 종료합니다.
- `echo $?`: 직전에 실행한 명령의 Shell 종료 상태를 확인합니다. `0`은 해당 명령의 정상 종료를 나타냅니다.

**전달받은 실행 요약(원본 전체 로그 미보관):**

```text
992 .bb files
2013 targets
73 skipped
0 errors
echo $? -> 0
```

| 결과 | 이 기록에서 확인 가능한 범위 |
|---|---|
| 992 `.bb` files | BitBake가 보고한 Recipe 파일 수 |
| 2013 targets | 파싱 결과 제공 가능한 Target 항목 수. 각각의 빌드 성공을 뜻하지 않음 |
| 73 skipped | BitBake가 건너뛴 Recipe 수. 개별 제외 사유는 이 요약에 없음 |
| 0 errors / Exit code 0 | Parse 단계 정상 종료 |
| 실제 컴파일·이미지 생성 | **미검증** |

### 9.2 WSL2 경고와 제약

실행 중 `WARNING: You are running bitbake under WSLv2...` 메시지가 보고되었습니다. **경고와 오류를 구분**해야 하며, 이번 Parse 명령은 종료 코드 0으로 끝났습니다. 경고 메시지의 전체 내용은 보관되지 않았으므로 구체적인 원인이나 조치 여부를 임의로 단정하지 않습니다.

집 노트북은 센터보다 RAM이 작아 병렬도를 `2 / -j 2`로 낮춰 사용합니다. 이미지 빌드를 시작하기 전 WSL2 가상 디스크와 Host의 여유 공간을 확인해야 합니다. `bitbake -p` 성공만으로 빌드에 필요한 메모리·디스크 용량이 충분하다고 판정할 수 없습니다.

### 9.3 검증 범위와 다음 단계

집에서도 Build Environment 구성과 Recipe Parse의 정상 종료를 확인했습니다. 다음 Chapter에서는 `bitbake-layers show-recipes busybox`로 Recipe 제공 정보를 조회할 예정이며, **이 명령은 아직 수행 완료로 기록하지 않습니다.**

집 노트북과 센터의 서로 다른 병렬 설정은 [빌드 설정](../configs/build-config.md), 학교↔집 BitBake Checkout 대조 범위는 [소스 리비전](../configs/source-revisions.md)에 각각 관리합니다.

## 참고 문서

- [Yocto Project 6.0 — Setting Up to Use the Yocto Project](https://docs.yoctoproject.org/6.0/dev-manual/start.html)
- [Yocto Project 6.0 — Quick Build](https://docs.yoctoproject.org/6.0/brief-yoctoprojectqs/index.html)
- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
- [BitBake 2.16 — Command options, `-p` / `--parse-only`](https://docs.yoctoproject.org/bitbake/2.16/bitbake-user-manual/bitbake-user-manual-intro.html)
