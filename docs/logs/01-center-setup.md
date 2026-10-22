# Chapter 1 — 센터 실행 기록 및 검증 근거

> 센터 WSL2 Ubuntu (`kccistc`) · 기록 정리 기준: 2026-10-22  
> Yocto Project 6.0.4 (wrynose) · Target: Raspberry Pi 4B (ARM64)

이 문서는 [Chapter 1 개발 환경 구성](../01-environment.md)의 **증거 기록**입니다. 실행 절차와 변수 설명은 Chapter 1에 두고, 여기서는 관측 결과와 증거의 한계를 분리합니다.

## 증거 분류

- **[원문 발췌]**: 이전 실습 대화에 보존된 터미널 출력의 일부를 원문과 대조해 발췌했습니다. 반복 행은 생략했으며 이를 전체 로그라고 표기하지 않습니다.
- **[검증 결과 기록]**: 이전 실습 요약 또는 GitHub 문서에 확인 결과가 남았지만 출력 전문은 확보되지 않았습니다.
- **[미확인]**: 해당 실행/성공에 대한 충분한 증거가 없습니다.

아래에 포함된 로그 시각은 **터미널 출력에 기록된 시각**이며, 정확한 실행 날짜를 독립적으로 검증한 결과는 아닙니다. 집 노트북의 실행 결과는 이 문서에 혼합하지 않습니다.

## 1. BitBake 초기화 중 Locale 오류 — [원문 발췌]

### 현상

`bitbake-setup init`에서 초기 Configuration Fragment를 활성화하던 중 BitBake 서버가 시작되지 않았습니다.

**기존 대화에서 확인된 출력 발췌:**

```text
Setting up bitbake configuration in
    /home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build

ERROR: Execution of 'bash -c '. /home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/init-build-env && bitbake-config-build enable-fragment distro/poky machine/qemuarm64'' failed with exit code 1:
ERROR: Unable to start bitbake server (None)
ERROR: Server didn't start, last 60 loglines (/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/bitbake-cookerdaemon.log):
Please make sure locale 'en_US.UTF-8' is available on your system

NOTE: Retrying server connection (#1)... (12:18:24.461843)
```

동일한 Locale 오류는 여러 차례 반복되었습니다. 아래는 원문 후반부 발췌입니다.

```text
NOTE: Retrying server connection (#8)... (12:18:48.108235)
ERROR: Unable to connect to bitbake server, or start one (server startup failures would be in bitbake-cookerdaemon.log).
```

### 원인·판정

- 메시지가 `en_US.UTF-8` Locale 이용 불가를 직접 가리키므로, **필요한 Locale이 준비되지 않은 상태**가 서버 시작 실패의 확인된 원인입니다.
- 초기 설정 단계는 종료 코드 `1`로 **실패**했습니다. 따라서 이 출력 자체를 환경 구성 성공의 증거로 사용하지 않습니다.
- 출력에 `init-build-env` 호출이 포함되지만, 이는 **초기화 명령의 내부 실행 과정**입니다. 사용자가 이를 별도로 수동 `source`했다는 증거는 아닙니다.

## 2. Locale 생성 및 정상화 — [검증 결과 기록]

기존 실습 문서에 기록된 수정 명령:

```bash
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
```

기존 실습에서 확인했다고 보고된 출력·값:

```text
en_US.UTF-8... done
```

```text
en_US.utf8
```

`locale -a`에서 `en_US.utf8`을 확인했고, 이후 환경 구성이 진행되었다는 **검증 결과 기록**이 있습니다. 현재 확보된 자료에는 Locale 생성부터 복구까지 이어지는 **하나의 연속된 터미널 출력 전문은 없습니다**.

## 3. Raspberry Pi BSP Layer 등록 — [검증 결과 기록]

기존 수행 명령:

```bash
git clone -b wrynose https://git.yoctoproject.org/meta-raspberrypi ../layers/meta-raspberrypi
bitbake-layers add-layer ../layers/meta-raspberrypi
bitbake-layers show-layers
```

센터에서 확인된 Layer/Priority 값 (원본 `show-layers` 테이블 전문은 미확보):

| Layer | Priority |
|---|---:|
| `core` | 5 |
| `yoctobsp` | 5 |
| `yocto` | 5 |
| `raspberrypi` | 9 |

기존 기록에 따라 BSP Layer 등록·인식 완료로 판정합니다. 실제 Layer 경로와 목록 출력 전문까지 복원한 것은 아닙니다.

## 4. Target Machine 설정 — [검증 결과 기록]

기존 수행·확인 명령:

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
bitbake -e | grep -E '^(MACHINE|MACHINE_ARCH|DISTRO|DISTRO_VERSION)='
```

기존에 검증한 결과값 (원문 터미널 출력 전문은 미확보):

```text
DISTRO="poky"
DISTRO_VERSION="6.0.4"
MACHINE="raspberrypi4-64"
MACHINE_ARCH="raspberrypi4_64"
```

초기 `qemuarm64`에서 Raspberry Pi 4B ARM64 대상으로 변경했음을 확인한 기록입니다.

## 5. 빌드 병렬도 — [검증 결과 기록]

센터 WSL의 당시 기록: RAM 약 `15GiB`, 논리 CPU `24`개.

`build/conf/local.conf`에 적용한 설정:

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

`bitbake -e`에서 적용된 값을 확인했다는 실습 기록이 남아 있지만 **해당 명령의 원문 출력 전체는 미확보**입니다. 이는 **센터** 설정이며 집 노트북의 `2 / -j 2` 설정과 구분합니다.

## 6. Source Revision — [검증 결과 기록]

| 대상 | 센터 기록 SHA / 상태 |
|---|---|
| 최초 독립 Clone한 BitBake | `3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e` |
| OpenEmbedded-Core | `636e5d3b12d54951c13d57346648bc29a0e6b24e` |
| meta-raspberrypi | `919588393f41b48cb6c5d832aa35e58a19b6762d` |
| meta-yocto | **SHA 미확보** |
| 실제 Setup에서 사용하는 BitBake Checkout | **별도 SHA 미확보** |

이 값은 센터의 기존 소스 버전 **기록**으로, 이번 문서 작업에서 센터의 실제 Git Checkout을 다시 조회한 것이 아닙니다. 최초 Clone한 BitBake와 Setup에서 사용하는 BitBake는 **경로/Checkout을 구분하여 검사해야** 합니다. 최초 Clone의 SHA를 실제 Setup의 SHA로 대체해서 기재하지 않습니다.

상세 비교 방법은 [소스 리비전 문서](../../configs/source-revisions.md)를 참조합니다.

## 7. 미검증 및 완료 범위

| 항목 | 센터에서 확인된 상태 | 증거 유형 |
|---|---|---|
| 초기 BitBake 서버 Locale 오류 | 발생 확인 | 원문 발췌 |
| Locale 생성·정상화 | 완료 기록 | 검증 결과 기록 |
| BSP Layer 등록 및 Priority | 완료 기록 | 검증 결과 기록 |
| `MACHINE=raspberrypi4-64` | 적용 확인 기록 | 검증 결과 기록 |
| 병렬도 `4 / -j 4` | 적용 확인 기록 | 검증 결과 기록 |
| 센터 `bitbake -p` | 성공 로그 없음 | 미확인 |
| `core-image-minimal` 이미지 빌드 | 미진행 | 수행 기록 없음 |
| Raspberry Pi 4B 부팅 | 미진행 | 실장비 증거 없음 |

**증거 판정:** 센터 Chapter 1의 환경 설정과 확인 결과는 기록되어 있지만, 모든 단계의 터미널 출력 전문이 확보된 것은 아닙니다. 집 WSL에서 확인한 `bitbake -p` 성공은 [Chapter 1의 집 검증 절](../01-environment.md#9-집-노트북-환경-구성-및-recipe-parse-검증-추가-기록)에 별도로 보존합니다.
