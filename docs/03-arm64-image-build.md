# Chapter 3 — ARM64 Image Build

> **실습일:** 2026-10-25  
> **대상:** Raspberry Pi 4 Model B / Yocto 6.0.4 `wrynose` / `MACHINE=raspberrypi4-64`  
> **결과:** `core-image-minimal` 최초 빌드 성공(4,025/4,025 Tasks), 주요 산출물 형식 확인, Wic bzip2 압축 무결성 검사 통과  
> **범위:** 이미지 빌드와 산출물 검증. 실장비 부팅은 [Chapter 5](05-raspberrypi-boot.md)에서 별도 검증.

## 핵심 성과

| 항목 | 실제 결과 | 확인 근거 |
|---|---|---|
| 첫 이미지 빌드 | 4,025 Tasks 모두 성공 | BitBake 종료 로그 |
| 경고 추적 | Kernel metadata Fetch 초기 실패 → 최종 성공 | `grep`으로 WARNING 및 `do_fetch` 추적 |
| 타깃 이미지 | ARM64 Kernel, Pi 4B DTB, ext3 RootFS, Wic | `ls -lh`, `file -L` |
| 압축 검사 | `Wic compressed image: OK` | `bzip2 -t` |
| 미측정 항목 | 빌드 중 Peak 자원 사용량·정확한 소요 시간 | 실측 기록 없음 |

**핵심 판단:** 빌드 성공 메시지에만 의존하지 않고 경고가 발생한 Task의 최종 결과, 배포 디렉터리의 산출물, 실제 파일 시그니처, 압축 스트림을 각각 확인했다.

## 1. 환경과 경로

이 문서의 명령과 출력은 **센터 WSL**에서 기록했다. 집 WSL(`triton`)의 경로와 병렬도는 혼용하지 않는다. 기존 GitHub [Chapter 1](01-environment.md) 및 [Chapter 2](02-bitbake-layer-recipe.md)는 이전 단계의 기록이므로, 당시 이미지 빌드 미완료 표기와 이 장의 후속 빌드 성공은 모순이 아니다.

| 항목 | 기록값 |
|---|---|
| Host | 센터 Windows + WSL2 Ubuntu **22.04** (GitHub Chapter 1 및 Chapter 5의 센터 환경 기록 기준). Chapter 3 초안의 26.04 표기는 집 환경과 혼동된 것으로 판단되며, Chapter 3 실습 당시 OS 버전을 별도 명령으로 재조회한 기록은 없다. |
| Host 사용자 | `kccistc` |
| Yocto / DISTRO | Poky 6.0.4 `wrynose` / `poky` |
| BitBake | 2.18.0 (이전 챕터 인수인계) |
| Target | Raspberry Pi 4B, ARM64 |
| MACHINE | `raspberrypi4-64` |
| 병렬도 | `BB_NUMBER_THREADS="4"`, `PARALLEL_MAKE="-j 4"` (센터 직접 확인) |

```text
BUILD_DIR=/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
DEPLOY_DIR=/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/deploy/images/raspberrypi4-64
SOURCE_REPO=/home/kccistc/study/rootfs/yocto/yocto-rpi4-lab
BUILD_LOG=/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/chapter-03-build.log
```

> **증거 구분:** 아래 로그는 당시 ChatGPT 학습 대화에 제공된 실제 출력의 핵심 부분이다. 전체 `ls -lh` 269줄 출력과 원본 빌드 로그 전체를 이 문서에 재수록한 것은 아니다. 명령 입력 화면이 남지 않은 경우는 실제 입력 명령을 추정해 확정하지 않는다.

## 2. 빌드 전 Host 자원 확인

**CWD:** `BUILD_DIR`

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
pwd
nproc
free -h
df -h . /mnt/c
```

**실제 출력:**

```text
/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
24
               total        used        free      shared  buff/cache   available
Mem:            15Gi       556Mi        13Gi       3.0Mi       1.2Gi        14Gi
Swap:          4.0Gi          0B       4.0Gi
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdd       1007G   17G  940G   2% /
C:\             465G  262G  203G  57% /mnt/c
```

WSL의 `/dev/sdd`가 표시한 여유 940G는 Linux 파일시스템 관점의 값이다. WSL 가상 디스크가 Windows C 드라이브에 저장된다면 실제 호스트 여유 공간(203G)이 제약이 될 수 있다. 이 출력은 **빌드 시작 전** 상태이며 Peak CPU/RAM/디스크 사용량은 측정하지 않았다.

## 3. BitBake 환경과 산출물 경로

### 3.1 병렬도 확인

**CWD:** `BUILD_DIR`

```bash
source ./init-build-env
bitbake -e core-image-minimal | grep -E '^(BB_NUMBER_THREADS|PARALLEL_MAKE)='
```

```text
Poky - The Yocto Project testing distribution
BB_NUMBER_THREADS="4"
PARALLEL_MAKE="-j 4"
```

`BB_NUMBER_THREADS`는 동시에 처리하는 BitBake Task의 상한이며, `PARALLEL_MAKE`는 해당 값을 활용하는 빌드 도구의 작업 병렬도를 설정한다. 두 값은 동일한 개념이 아니다.

### 3.2 주요 설정 조회

**실제 CWD:** `SOURCE_REPO` (명령 출력의 절대 경로는 `BUILD_DIR`를 가리킴). 해당 셸의 환경 유지 경로는 별도 조사하지 않았다.

```bash
bitbake -e core-image-minimal | \
  grep -E '^(MACHINE|DISTRO|TMPDIR|DL_DIR|SSTATE_DIR|DEPLOY_DIR_IMAGE|IMAGE_FSTYPES|WKS_FILE)='
```

```text
DEPLOY_DIR_IMAGE="/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/deploy/images/raspberrypi4-64"
DISTRO="poky"
DL_DIR="/home/kccistc/study/rootfs/yocto/bitbake-builds/.bitbake-setup-downloads"
IMAGE_FSTYPES="tar.bz2 ext3 wic.bz2 wic.bmap"
MACHINE="raspberrypi4-64"
SSTATE_DIR="/home/kccistc/study/rootfs/yocto/bitbake-builds/.sstate-cache"
TMPDIR="/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp"
WKS_FILE="sdimage-raspberrypi.wks"
```

| 변수 | 역할 |
|---|---|
| `MACHINE` | 타깃 보드 및 하드웨어 구성 선택 |
| `DISTRO` | 배포판 정책 선택 |
| `TMPDIR` | 작업 디렉터리 및 빌드 결과 |
| `DL_DIR` | 다운로드 소스 캐시 |
| `SSTATE_DIR` | 공유 상태 캐시 |
| `DEPLOY_DIR_IMAGE` | 이미지·커널 등 배포 산출물 |
| `IMAGE_FSTYPES` | 요청한 RootFS/디스크 이미지 형식 |
| `WKS_FILE` | Wic 파티션 배치 명세의 파일 이름 |

Chapter 2에서는 집 환경에서 `core-image-minimal.bb`, `packagegroup-core-boot.bb`, `rpi-base.inc`의 역할을 분석했다. **그 파일을 센터에서 다시 읽은 것으로 기록하지 않는다.** 센터의 최종 설정은 위 `bitbake -e` 출력으로 확인했다.

## 4. 최초 이미지 빌드

**빌드 기준 CWD:** `BUILD_DIR`. 다음은 당시 제안된 출력 보존 방식이다. **사용자가 실제 입력한 명령 문자열 전체가 별도 캡처된 것은 아니다.**

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
set -o pipefail
bitbake core-image-minimal 2>&1 | tee chapter-03-build.log
```

`tee`는 출력 표시와 파일 저장을 병행한다. `pipefail`은 `tee`가 정상 종료하더라도 앞선 BitBake 실패를 놓치지 않도록 한다.

**실제 빌드 종료 출력:**

```text
NOTE: Running noexec task 4025 of 4025 (/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta/recipes-core/images/core-image-minimal.bb:do_build)
NOTE: Tasks Summary: Attempted 4025 tasks of which 0 didn't need to be rerun and all succeeded.

Summary: There was 1 WARNING message.
```

**해석:** 총 4,025개 Task의 빌드가 성공했다. `0 didn't need to be rerun`은 이 요약에서 재실행이 불필요해 건너뛴 Task가 0개라는 뜻이다. `do_build`는 최종 종합 Task이며 여기서는 `noexec`으로 표시되므로 마지막 단계에서 별도 컴파일이 실행됐다는 의미는 아니다. 이는 **빌드 성공**의 증거이지, 아직 **실장비 부팅 성공**의 증거는 아니다.

### 빌드 중 관찰한 SPDX Task

```text
NOTE: recipe tar-native-1.35-r0: task do_create_package_spdx: Started
NOTE: recipe tar-native-1.35-r0: task do_create_package_spdx: Succeeded
NOTE: recipe parted-native-3.6-r0: task do_create_package_spdx: Started
NOTE: recipe parted-native-3.6-r0: task do_create_package_spdx: Succeeded
```

`do_create_package_spdx`는 소프트웨어 구성·라이선스 관련 메타데이터 생성 Task이다. `-native`는 빌드 호스트용 도구를 의미한다. 이 일부 Task의 성공만으로 전체 이미지 빌드 완료를 판단하지는 않았다.

## 5. WARNING 원인 범위와 최종 결과 추적

**CWD:** `BUILD_DIR`, **조회 파일:** `BUILD_LOG`

```bash
grep -n -C 5 'WARNING:' chapter-03-build.log
```

```text
5819-NOTE: Running task 1939 of 4025 (/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta/recipes-devtools/elfutils/elfutils_0.194.bb:do_configure)
5820-NOTE: recipe elfutils-0.194-r0: task do_configure: Started
5821:WARNING: linux-raspberrypi-1_6.18.33+git-r0 do_fetch: Failed to fetch URL git://git.yoctoproject.org/yocto-kernel-cache;type=kmeta;name=meta;branch=yocto-6.18;destsuffix=kernel-meta, attempting MIRRORS if available
5822-NOTE: recipe xz-5.8.2-r0: task do_package: Succeeded
```

원래 URL의 Fetch 실패와 대체 경로 시도가 기록되었다. **실제 Mirror URL이나 최초 실패 원인은 이 출력만으로 확인할 수 없다.**

```bash
grep -n 'linux-raspberrypi.*task do_fetch:' chapter-03-build.log
```

```text
3197:NOTE: recipe linux-raspberrypi-1_6.18.33+git-r0: task do_fetch: Started
6706:NOTE: recipe linux-raspberrypi-1_6.18.33+git-r0: task do_fetch: Succeeded
```

**판정:** 경고 발생 후 해당 `do_fetch`는 최종 성공했으며 전체 이미지 빌드도 성공했다. 이 증거만으로 추가 설정 변경이나 재빌드가 필요한 오류라고 보지 않는다.

## 6. 배포 산출물 확인

**CWD:** `BUILD_DIR`

```bash
ls -lh tmp/deploy/images/raspberrypi4-64/
```

당시 출력은 `total 99M`으로 시작했고, 269줄 규모의 전체 목록은 별도 첨부 `붙여넣은 텍스트(1).txt`로 보존했다. 아래는 원문에 확인된 주요 파일만 추린 것이다.

| 산출물 | 관찰 크기 | 역할 |
|---|---:|---|
| `Image` → `Image-1-6.18.33+git0+6d012fbc35_95b85bebbe-r0-raspberrypi4-64-20261025055346.bin` | 26M | ARM64 Linux Kernel |
| `bcm2711-rpi-4-b.dtb` | 56K | Raspberry Pi 4B DTB |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.ext3` | 28M | ext3 RootFS |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.tar.bz2` | 5.7M | 압축 RootFS 아카이브 |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.wic.bz2` | 29M | 압축 Wic 디스크 이미지 |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.wic.bmap` | 3.0K | Wic 기록용 블록 맵 |
| `modules-1-6.18.33+git0+6d012fbc35_95b85bebbe-r0-raspberrypi4-64-20261025055346.tgz` | 20M | 커널 모듈 아카이브 |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.manifest` | 908 B | 설치 패키지 목록(내용 미조회) |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.spdx.json` | 1.8M | SPDX 데이터(내용 미조회) |
| `core-image-minimal-raspberrypi4-64.rootfs-20261025055346.testdata.json` | 294K | 테스트 데이터(내용 미조회) |
| `bootfiles/` | 디렉터리 | 부팅 파일(내부 목록 미조회) |

`Image` 및 단축 이름으로 제공되는 일부 산출물은 버전·타임스탬프가 포함된 실제 파일을 가리키는 심볼릭 링크다. `total 99M`은 배포 디렉터리 전체 사용량의 요약으로, 단일 Wic 이미지 크기가 아니다. `.dtbo`, `grub-efi-bootaa64.efi`, `systemd-bootaa64.efi` 등의 존재는 해당 기능이나 부트로더가 **실제 Pi에서 실행됐다**는 증거가 아니다. `modules-*.tgz`의 존재 역시 모듈이 RootFS에 설치됐다는 증거는 아니다.

## 7. 파일 시그니처 확인

**CWD:** `BUILD_DIR`

```bash
file -L tmp/deploy/images/raspberrypi4-64/{Image,bcm2711-rpi-4-b.dtb,core-image-minimal-raspberrypi4-64.rootfs.ext3,core-image-minimal-raspberrypi4-64.rootfs.wic.bz2}
```

**실제 출력:**

```text
tmp/deploy/images/raspberrypi4-64/Image:                                             Linux kernel ARM64 boot executable Image, little-endian, 4K pages
tmp/deploy/images/raspberrypi4-64/bcm2711-rpi-4-b.dtb:                               Device Tree Blob version 17, size=56407, boot CPU=0, string block size=4923, DT structure block size=51412
tmp/deploy/images/raspberrypi4-64/core-image-minimal-raspberrypi4-64.rootfs.ext3:    Linux rev 1.0 ext3 filesystem data, UUID=bc4f7a69-29a0-4112-a2a8-48c0237caa1a (large files)
tmp/deploy/images/raspberrypi4-64/core-image-minimal-raspberrypi4-64.rootfs.wic.bz2: bzip2 compressed data, block size = 900k
```

`file -L`은 심볼릭 링크의 실제 대상을 따라가 파일 시그니처를 확인한다. 이 단계에서 ARM64 커널 이미지, DTB v17, ext3 RootFS, bzip2 압축 파일을 식별했다. 단, bzip2의 `block size = 900k`는 압축 블록 크기이며 RootFS나 파티션 크기가 아니다. 압축본의 내부 파티션 구조는 이 명령만으로 판단할 수 없다.

## 8. Wic 압축 무결성 확인

**CWD:** `BUILD_DIR`

```bash
bzip2 -t tmp/deploy/images/raspberrypi4-64/\
core-image-minimal-raspberrypi4-64.rootfs.wic.bz2 \
  && echo "Wic compressed image: OK"
```

**실제 출력:**

```text
Wic compressed image: OK
```

`bzip2 -t`가 압축 스트림을 읽어 검사했고 성공했음을 뜻한다. 이 결과만으로 Wic 파티션·RootFS 내용·실장비 부팅까지 검증됐다고 주장하지 않는다.

## 9. 기술적으로 확인한 것과 남은 범위

| 검증 항목 | Chapter 3 당시 상태 | 후속 연결 |
|---|---|---|
| BitBake 성공 로그 | 확인 | §4 |
| Fetch 경고의 최종 성공 | 확인 | §5 |
| 커널·DTB·RootFS·Wic 산출물 | 확인 | §6–7 |
| Wic 압축 무결성 | 확인 | §8 |
| 압축 해제 Wic 파티션 구성 | 당시 미검증 | Chapter 5 §3에서 수행 |
| RootFS 패키지/Recipe 역추적 | 미검증 | Chapter 4 과제 |
| 실제 Pi 부팅 | 당시 미실행 | Chapter 5에서 성공 |
| 빌드 중 자원 Peak·정확한 소요 시간 | 미측정 | 기록 없음 |
| 최초 Fetch 실패 원인·실제 Mirror | 미확인 | 필요 시 별도 분석 |
| 이미지 SHA-256 | 당시 미계산 | 기록 없음 |

### Chapter 5와의 정확한 연결

Chapter 3에서 생성한 최초 이미지의 타임스탬프는 **`20261025055346`**이다. Chapter 5에서는 최초 이미지로 로그인 프롬프트까지 확인한 후, 개발용 root 로그인 Fragment를 활성화하여 **`20261025083110`** 이미지로 다시 빌드하고 실제 로그인·네트워크·RootFS를 검증했다. 따라서 *Chapter 3의 최초 산출물이 설정 변경 없이 그대로 최종 로그인 검증에 사용됐다*고 표현하지 않는다.

Chapter 3의 `.ext3` 파일은 **별도 RootFS 산출물**이고, Chapter 5의 ext4는 **SD에 기록한 Wic 이미지로 부팅한 뒤 관찰한 루트 마운트**다. 서로 다른 검증 대상이므로 파일 확장자만으로 Wic 내부 루트 파티션의 파일시스템 형식을 단정하지 않는다.

## 10. 학습 결과 및 다음 단계

이번 장에서는 Yocto 이미지 빌드가 단순 C 컴파일을 넘어 Recipe의 Fetch·Compile·Packaging·RootFS·이미지 조립 Task를 연결한다는 점을 실제 결과로 확인했다. Host용 Native Tool과 ARM64 Target용 Cross Toolchain을 구별했고, 산출물 파일의 존재와 실제 장비에서의 동작을 별개 증거로 관리했다.

- **Chapter 4:** RootFS의 파일·설치 패키지를 `.manifest` 및 Recipe와 연결해 분석.
- **Chapter 5:** [Raspberry Pi 4B UART 부팅, 로그인 문제 해결, 네트워크·커널 모듈 선행 검증](05-raspberrypi-boot.md).

> **기록 범위:** 이 문서는 실제 제공된 명령·출력과 그 기술적 해석을 구분한다. 측정하지 않은 시간·자원 사용량이나 확인되지 않은 Mirror URL은 추가하지 않았다.
