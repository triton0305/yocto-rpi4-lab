# Chapter 1 — 집 WSL2 실행 기록 및 검증 근거

> 환경: Windows 11 / WSL2 Ubuntu 26.04.1 LTS (`triton`)  
> 실습 시점: 2026-10-22 ~ 2026-10-23 (KST, 대화 기록 기준)  
> Yocto 6.0.4 (wrynose) · `DISTRO=poky` · `MACHINE=raspberrypi4-64` · Target: Raspberry Pi 4B (ARM64)

이 문서는 [Chapter 1 개발 환경 구성](../01-environment.md)의 **집 노트북 실행 증거**입니다. 아래 출력은 사용자가 대화에 제공한 기록을 기준으로 정리했으며, GitHub 문서 수정 과정에서 노트북에 원격 접속하거나 명령을 재실행하지 않았습니다. 센터 실습 근거는 [센터 로그](01-center-setup.md)와 별도 관리합니다.

## 기록 범위

- **[실행 로그]**: 사용자가 입력 명령과 출력 또는 해당 터미널 출력을 제공한 항목.
- **[출력 검증]**: 일부 수행 과정은 미보관이나 후속 조회 결과에서 설정이 확인된 항목.
- **[안내 명령]**: 실행을 안내했지만 개별 실행 출력은 미확보인 항목.
- **[미실행/미검증]**: 해당 작업의 성공을 증명할 출력이 없는 항목.

아래 `[발췌]` 표기는 제공된 출력의 일부만 수록했다는 의미입니다. 당시 Git 상태와 가용 저장 용량은 특정 시점의 스냅샷이며, 현재 상태를 보장하지 않습니다.

## 1. Host 자원 확인 — [실행 로그]

명령:

```bash
cat /etc/os-release
free -h
df -h ~ /mnt/c
nproc
```

출력:

```text
PRETTY_NAME="Ubuntu 26.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="26.04"
VERSION="26.04.1 LTS (Resolute Raccoon)"
VERSION_CODENAME=resolute
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=resolute
LOGO=ubuntu-logo
               total        used        free      shared  buff/cache   available
Mem:           7.6Gi       625Mi       6.3Gi       3.5Mi       905Mi       7.0Gi
Swap:          2.0Gi          0B       2.0Gi
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdd       1007G  9.0G  947G   1% /
C:\             219G  149G   70G  68% /mnt/c
8
```

**판정:** 논리 CPU 8개, RAM 7.6GiB, Swap 2.0GiB. 당시 Windows C: 가용 공간은 `70G`로 보고되었습니다. Linux `/dev/sdd`에 표시된 `947G`는 WSL 파일시스템의 논리적 여유 공간이며, Windows 물리 디스크 여유 공간이 그만큼 확보되었다는 뜻은 아닙니다.

## 2. 초기 BitBake Clone의 위치와 SHA — [실행 로그]

최초 `~/bitbake`에서 Clone·Checkout한 다음 `~/study/rootfs/yocto/bitbake`로 옮겼다는 작업 기록이 있으나 **Clone·이동의 출력 전문은 확보되지 않았습니다.** 최종 경로와 SHA는 조회로 확인했습니다.

```bash
cd ~/study/rootfs/yocto
git -C bitbake rev-parse HEAD
ls
```

```text
3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e
bitbake
```

**판정:** 최상위 BitBake Clone HEAD 확인. 실제 Setup이 설치한 내부 BitBake Checkout의 버전은 10절에서 별도 확인합니다.

## 3. GitHub 학습 저장소 연결 — [실행 로그]

`git clone`의 출력 자체는 미확보이며, 이후 실제 조회 출력은 다음과 같습니다.

```bash
cd ~/study/rootfs/yocto/yocto-rpi4-lab
git status -sb
git log -1 --oneline
```

```text
## main...origin/main
9006b48 (HEAD -> main, origin/main, origin/HEAD) docs: clarify Yocto setup, configuration and revision evidence
```

**판정:** 집 노트북에 학습 저장소가 있고, **그 시점에** `main` 및 `origin/main`이 `9006b48`을 가리켰습니다. `git status -sb`의 출력에는 변경 파일이 없어 당시 작업 트리는 깨끗했습니다. 이는 **현재 GitHub HEAD를 뜻하지 않습니다.**

## 4. UTF-8 Locale 정상화

### 4.1 초기 조회 — [실행 로그]

```bash
locale -a | grep en_US
```

출력 없음. 당시 `en_US` Locale을 찾지 못했습니다. Locale 이름 자체를 실행 명령으로 입력하여 발생한 다음 오류도 기록되었습니다.

```text
en_US.utf8: command not found
```

`en_US.utf8`은 명령이 아닌 Locale 식별자이므로 별개의 단순 명령 입력 오류입니다.

### 4.2 안내된 해결 명령 — [안내 명령]

아래 명령의 **개별 실행 로그 전문은 확보되지 않았습니다.**

```bash
sudo sed -i \
  's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' \
  /etc/locale.gen
sudo locale-gen
sudo update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### 4.3 정상 상태 확인 — [실행 로그]

```bash
locale -a | grep en_US
locale | grep -E '^(LANG|LC_ALL)='
```

```text
en_US.utf8
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8
```

**판정:** 해당 Shell에서 Locale 생성 및 환경변수 적용 상태가 확인됐습니다. 이후 BitBake Parse가 정상 완료됐으므로 Locale 문제로 인해 진행이 막히지 않았습니다.

## 5. Setup 초기화 및 중복 생성 — [실행 로그]

### 5.1 최초 Setup 생성

실행 위치: `~/study/rootfs/yocto`

```bash
./bitbake/bin/bitbake-setup init \
  --non-interactive \
  poky-wrynose poky distro/poky machine/qemuarm64
```

당시 제공된 출력:

```text
NOTE: Bitbake-setup is using /home/triton/study/rootfs/yocto/bitbake-builds as top directory.
/home/triton/study/rootfs/yocto/bitbake-builds looks like a new top directory. If you would like to use a different directory, answer "n" below and either:
        1) Change the default bitbake-setup settings:
                bitbake-setup settings set default top-dir-prefix <PATH>
                bitbake-setup settings set default top-dir-name <NAME>
        2) Pass one or more options on the command line to change the top level directory in that invocation only:
                bitbake-setup --setting default top-dir-prefix <PATH> ...
                bitbake-setup --setting default top-dir-name <NAME> ...

A common site.conf file will be created, please check it is correct before running builds
    /home/triton/study/rootfs/yocto/bitbake-builds/site.conf

NOTE: Looking up config poky-wrynose in configuration registry
NOTE: Run 'bitbake-setup init --non-interactive poky-wrynose poky distro/poky machine/qemuarm64' to select this configuration non-interactively.

Initializing a setup directory in
    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose
Fetching layer/tool repositories into /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers
    bitbake
    openembedded-core
    meta-yocto
    yocto-docs

Setting up bitbake configuration in
    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build

This bitbake configuration provides:
    Poky - The Yocto Project testing distribution

Usage instructions and additional information are in
     /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/README

To run builds, source the environment using
    . /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/init-build-env

Run 'bitbake-config-build enable-fragment <fragment-name>' to enable additional fragments or replace built-in ones (e.g. machine/<name> or distro/<name> to change MACHINE or DISTRO).

The bitbake configuration files (local.conf, bblayers.conf and more) can be found in
    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/conf

To edit the code in VSCode, open the workspace:
    code /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/bitbake.code-workspace
```

**판정:** 최초 `poky-wrynose` Setup이 생성됐고 `poky` Distribution과 `qemuarm64` 초기 Target을 사용했습니다. 위 출력 자체에는 오류가 없고, 이후 `init-build-env` 및 BitBake 실행도 확인됐습니다.

### 5.2 같은 명령을 다시 실행한 경우 — [실행 로그 발췌]

동일한 `bitbake-setup init` 명령을 한 번 더 수행해 기존 Setup을 덮어쓰지 않고 두 번째 경로가 만들어졌습니다.

```text
NOTE: Bitbake-setup is using /home/triton/study/rootfs/yocto/bitbake-builds as top directory.
NOTE: A site.conf file already exists. Please remove it if you would like to replace it with a default one
NOTE: Looking up config poky-wrynose in configuration registry
NOTE: Run 'bitbake-setup init --non-interactive poky-wrynose poky distro/poky machine/qemuarm64' to select this configuration non-interactively.

NOTE: Setup directory /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose (as suggested by configuration) already exists, using the full name instead.

Initializing a setup directory in
    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64
Fetching layer/tool repositories into /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64/layers
    bitbake
    openembedded-core
    meta-yocto
    yocto-docs

Setting up bitbake configuration in
    /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64/build

This bitbake configuration provides:
```

**판정:** 기존 정상 Setup은 보존됐고 두 번째 Setup이 별도 디렉터리로 생성됐습니다.

## 6. 중복 Setup 정리 — [실행 로그]

두 디렉터리 확인:

```bash
cd ~/study/rootfs/yocto
ls -d bitbake-builds/poky-wrynose*
```

```text
bitbake-builds/poky-wrynose
bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64
```

정상 Setup 진입 스크립트의 존재도 확인:

```bash
ls -l bitbake-builds/poky-wrynose/build/init-build-env
```

```text
-rw-r--r-- 1 triton triton 238 Oct 23 00:16 bitbake-builds/poky-wrynose/build/init-build-env
```

최초 삭제 시도는 읽기 전용 Git 객체에 대한 확인 프롬프트에서 `Ctrl+C`로 중단했습니다.

```bash
rm -rI -- bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64
```

```text
rm: remove 1 argument recursively? y
rm: remove write-protected regular file 'bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64/config/.git/objects/0f/48ba0725e1d3352aa0a11a22a03080093a8342'? ^C
```

이후 **중복 경로만 지정해** 제거하고 재확인했습니다.

```bash
cd ~/study/rootfs/yocto
rm -rf -- bitbake-builds/poky-wrynose-poky-distro_poky-machine_qemuarm64
ls -d bitbake-builds/poky-wrynose*
```

```text
bitbake-builds/poky-wrynose
```

**판정:** 정상 Setup은 유지됐습니다. `rm -rf`는 **과거 문제 해결 기록**이지 일반 재현용 명령이 아닙니다. 검증 없이 반복 실행해서는 안 됩니다.

## 7. Build Environment 진입 및 초기 Layer — [실행 로그]

```bash
source bitbake-builds/poky-wrynose/build/init-build-env
pwd
command -v bitbake
bitbake-layers show-layers
```

```text
Poky - The Yocto Project testing distribution
/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
/home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/bitbake/bin/bitbake
NOTE: Starting bitbake server...
layer                 path                                                                    priority
========================================================================================================
core                  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta  5
yoctobsp              /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-yocto-bsp  5
yocto                 /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-poky  5
```

**판정:** Build Directory에 진입했고, 실제 실행되는 BitBake의 경로는 **`layers/bitbake/bin/bitbake`**입니다. BSP 추가 이전에는 Priority 5의 Layer 3개가 등록되어 있었습니다.

## 8. Raspberry Pi BSP Clone 및 특정 SHA 고정 — [실행 로그]

Build Directory에서 실행:

```bash
git clone -b wrynose \
  https://git.yoctoproject.org/meta-raspberrypi \
  ../layers/meta-raspberrypi
```

```text
Cloning into '../layers/meta-raspberrypi'...
remote: Enumerating objects: 12674, done.
remote: Counting objects: 100% (131/131), done.
remote: Compressing objects: 100% (125/125), done.
remote: Total 12674 (delta 73), reused 0 (delta 0), pack-reused 12543 (from 1)
Receiving objects: 100% (12674/12674), 3.85 MiB | 2.81 MiB/s, done.
Resolving deltas: 100% (7450/7450), done.
```

```bash
git -C ../layers/meta-raspberrypi checkout \
  919588393f41b48cb6c5d832aa35e58a19b6762d
```

출력 [중요 내용 포함]:

```text
Note: switching to '919588393f41b48cb6c5d832aa35e58a19b6762d'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

HEAD is now at 9195883 entrypoint-build.sh: Fix bitbake branches
```

**판정:** `meta-raspberrypi`를 센터 기록과 동일한 SHA로 Checkout했습니다. 특정 Commit에 직접 Checkout하여 발생한 `detached HEAD` 안내는 오류가 아닙니다.

## 9. Layer 등록과 Machine 변경 — [실행 로그]

```bash
bitbake-layers add-layer ../layers/meta-raspberrypi
bitbake-layers show-layers
```

```text
NOTE: Starting bitbake server...
NOTE: Starting bitbake server...
layer                 path                                                                    priority
========================================================================================================
core                  /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/openembedded-core/meta  5
yoctobsp              /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-yocto-bsp  5
yocto                 /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-yocto/meta-poky  5
raspberrypi           /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/layers/meta-raspberrypi  9
```

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

```text
NOTE: Starting bitbake server...
Fragment machine/raspberrypi4-64 added to /home/triton/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/conf/toolcfg.conf.
```

```bash
bitbake -e | grep -E '^(MACHINE|MACHINE_ARCH|DISTRO|DISTRO_VERSION)='
```

```text
DISTRO="poky"
DISTRO_VERSION="6.0.4"
MACHINE="raspberrypi4-64"
MACHINE_ARCH="raspberrypi4_64"
```

**판정:** Clone(소스 확보), `add-layer`(Layer 등록), `enable-fragment`(Target 설정)은 구별되는 단계입니다. 4개 Layer 및 Raspberry Pi ARM64 Machine 적용을 확인했습니다.

## 10. 각 Git Checkout의 SHA — [실행 로그]

Build Directory에서 실행한 명령:

```bash
git -C ../layers/openembedded-core rev-parse HEAD
git -C ../layers/meta-yocto rev-parse HEAD
git -C ../layers/meta-raspberrypi rev-parse HEAD
git -C ../layers/bitbake rev-parse HEAD
```

출력 (명령 순서대로):

```text
636e5d3b12d54951c13d57346648bc29a0e6b24e
7c25b11156553145fa6b241a2d4f65d94438f804
919588393f41b48cb6c5d832aa35e58a19b6762d
6e260eb6ab1631607ea414d9ff8ede1155faa5d9
```

별도 최상위 Clone 조회:

```bash
git -C ../../../bitbake rev-parse HEAD
```

```text
3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e
```

| Checkout | 집 노트북에서 확인한 SHA |
|---|---|
| 초기 Setup 실행용 `~/study/rootfs/yocto/bitbake` | `3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e` |
| 실제 BitBake 실행 위치 `layers/bitbake` | `6e260eb6ab1631607ea414d9ff8ede1155faa5d9` |
| `layers/openembedded-core` | `636e5d3b12d54951c13d57346648bc29a0e6b24e` |
| `layers/meta-yocto` | `7c25b11156553145fa6b241a2d4f65d94438f804` |
| `layers/meta-raspberrypi` | `919588393f41b48cb6c5d832aa35e58a19b6762d` |

**주의:** BitBake SHA 둘이 다른 것은 **서로 다른 Checkout**을 조회했기 때문입니다. 오류라고 단정할 수 없고, 센터의 `layers/bitbake` SHA는 미확보이므로 이 부분의 학교·집 버전 일치는 미검증입니다.

## 11. 병렬도 — [출력 검증]

편집 과정의 전체 로그는 없지만 최종 BitBake 변수는 조회로 검증됐습니다.

```conf
BB_NUMBER_THREADS = "2"
PARALLEL_MAKE = "-j 2"
```

```bash
bitbake -e | grep -E '^(BB_NUMBER_THREADS|PARALLEL_MAKE)='
```

```text
BB_NUMBER_THREADS="2"
PARALLEL_MAKE="-j 2"
```

**판정:** WSL2 RAM 7.6GiB 환경을 고려해 병렬도를 `2 / -j 2`로 낮췄습니다. 전체 이미지 빌드의 안정성을 검증한 값은 아닙니다.

## 12. BitBake Recipe Parse — [실행 로그]

```bash
bitbake -p
```

```text
WARNING: You are running bitbake under WSLv2, this works properly but you should optimize your VHDX file eventually to avoid running out of storage space
Loading cache: 100% |########################################| Time: 0:00:00
Loaded 0 entries from dependency cache.
Parsing recipes: 100% |######################################| Time: 0:00:26
Parsing of 992 .bb files complete (0 cached, 992 parsed). 2013 targets, 73 skipped, 0 masked, 0 errors.

Summary: There was 1 WARNING message.
```

종료 상태 확인:

```bash
echo $?
```

```text
0
```

| 항목 | 실제 출력 |
|---|---:|
| Recipe Parse | 992 `.bb` files |
| Cached / Parsed | 0 / 992 |
| Targets | 2013 |
| Skipped | 73 |
| Masked | 0 |
| Errors | 0 |
| Warnings | 1 (WSL2 VHDX 관련) |
| Exit Code | 0 |

**판정:** Recipe 메타데이터 Parse를 정상 종료했습니다. `-p`는 Parse Only이므로 C 소스 컴파일, 전체 Linux 이미지 생성 또는 Raspberry Pi 부팅을 검증한 결과는 아닙니다. WSL2 경고는 이번 명령을 실패 처리하는 오류가 아니며, 실제 빌드 전에 Windows 가용 공간과 VHDX 확장 가능성을 검토해야 합니다.

## 13. 센터 대비와 남은 검증

| 항목 | 센터 기존 기록 | 집 노트북 실행 결과 |
|---|---|---|
| Ubuntu | 22.04 | 26.04.1 LTS |
| WSL2 RAM | 15GiB | 7.6GiB |
| 논리 CPU | 24 | 8 |
| 병렬도 | `4 / -j 4` | `2 / -j 2` |
| Yocto | 6.0.4 | 6.0.4 |
| `MACHINE` / `DISTRO` | `raspberrypi4-64` / `poky` | 동일 |
| 초기 BitBake Clone SHA | `3ccdabf1...` | 일치 |
| OpenEmbedded-Core SHA | `636e5d3b...` | 일치 |
| meta-raspberrypi SHA | `91958839...` | 일치 |
| meta-yocto SHA | 미확인 | `7c25b111...` |
| 실제 `layers/bitbake` SHA | 미확인 | `6e260eb6...` |
| `bitbake -p` | 센터 출력 미확보 | 992 Recipe / 0 Errors / Exit 0 |

| 검증 대상 | 상태 |
|---|---|
| Host 정보 / Git SHA / GitHub 연결 | **완료(제공된 출력 기준)** |
| Locale / Setup / 중복 정리 | **완료(제공된 출력 기준)** |
| Layer 등록 / Machine / 병렬도 | **완료(제공된 출력 기준)** |
| BitBake Recipe Parse | **완료(제공된 출력 기준)** |
| `core-image-minimal` 이미지 빌드 | **미진행** |
| Raspberry Pi 4B 실제 부팅 | **미진행** |

## 14. 문서 관리

- [Chapter 1](../01-environment.md): 개념, 실행 목적, 재현 명령 및 결과 요약
- [센터 로그](01-center-setup.md): 센터에서 확보한 원문 오류 및 검증 결과
- [Build Config](../../configs/build-config.md): 센터·집 설정 비교
- [Source Revisions](../../configs/source-revisions.md): Checkout별 SHA 추적
