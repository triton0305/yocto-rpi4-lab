# Yocto 소스 리비전 관리

학교와 집에서 같은 Yocto 개발 환경을 재현하기 위해 외부 Source의 Commit SHA를 관리합니다. 기본 SHA는 **센터의 기존 GitHub 문서에 기록된 값**입니다. 이후 집 노트북의 독립 BitBake Clone에 대해 동일 SHA가 확인되었다는 **사용자 제공 검증 결과**가 추가되었습니다. 실제 Build Environment가 참조하는 모든 Source Checkout을 GitHub 문서 수정 중 직접 대조한 것은 아닙니다.

## 1. 기본 구성

| 항목 | 기록 |
|---|---|
| Yocto Project | 6.0.4 (wrynose) |
| DISTRO | `poky` |
| MACHINE | `raspberrypi4-64` |
| Host / Target | WSL2 Ubuntu (x86-64) / Raspberry Pi 4B (ARM64) |
| 환경 구성 방식 | `bitbake-setup init` (`poky-wrynose` 선택 기록) |

## 2. 기존 문서에 기록된 Source Commit

| Repository | 기존에 기록된 Commit SHA | 이번 점검 상태 |
|---|---|---|
| BitBake | `3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e` | **집의 독립 Clone ↔ 센터 기록 일치(사용자 제공 결과)**. 실제 Setup의 BitBake 경로는 미대조 |
| OpenEmbedded-Core | `636e5d3b12d54951c13d57346648bc29a0e6b24e` | 로컬 Checkout 미대조 |
| meta-raspberrypi | `919588393f41b48cb6c5d832aa35e58a19b6762d` | 로컬 Checkout 미대조 |
| meta-yocto | **기록 없음** | 실제 Checkout에서 확인 필요 |

`meta-yocto` 값은 기존 문서의 `실제 명령 출력값 입력`이라는 미완성 문구 대신 **기록 없음**으로 표시했습니다. 임의의 SHA를 채우지 않았습니다.

집 노트북의 `~/study/rootfs/yocto/bitbake`에서 보고된 Commit은 센터 기록의 BitBake SHA와 일치합니다. 이는 **독립적으로 내려받은 BitBake 소스의 동일성**만 뒷받침하며, 집에서 `bitbake -p`를 수행한 실제 BitBake 실행 파일의 Checkout까지 이 SHA라고 단정하지 않습니다.

Commit SHA만 기록해서는 설치 패키지, Host 환경, 로컬 설정까지 동일하다고 단정할 수 없습니다. 각 저장소의 Remote URL, Branch, Commit을 함께 점검해야 합니다.

## 3. 로컬 Checkout 대조 절차 (미실행 점검 명령)

먼저 이 프로젝트에서 사용한 Setup의 Build Environment를 준비합니다.

```bash
cd ~/study/rootfs/yocto
source bitbake-builds/poky-wrynose/build/init-build-env
bitbake-layers show-layers
```

`show-layers` 출력에서 Layer의 실제 디렉터리를 확인한 뒤, **각 Git 저장소 최상위 디렉터리**에 대해 아래 명령으로 정보를 수집합니다.

```bash
git -C ../layers/openembedded-core remote -v
git -C ../layers/openembedded-core branch --show-current
git -C ../layers/openembedded-core rev-parse HEAD

git -C ../layers/meta-raspberrypi remote -v
git -C ../layers/meta-raspberrypi branch --show-current
git -C ../layers/meta-raspberrypi rev-parse HEAD
```

위 상대 경로는 기존에 기록된 `poky-wrynose/build` 구조를 기준으로 한 **점검 예시**입니다. 실제 Source 위치가 다르면 `show-layers` 결과에 맞게 변경해야 합니다.

`meta-yocto`와 **실제 빌드에 사용되는 BitBake Git Checkout** 역시 현지 디렉터리를 확인한 다음 같은 `git -C <repository-path> ...` 명령으로 조사합니다. 최초 `git clone`한 `~/study/rootfs/yocto/bitbake`의 Commit이 실제 Setup에서 사용 중인 BitBake와 같다고 가정하지 않습니다.

## 4. 재현할 때 함께 비교할 사항

- Remote URL · Branch · Commit SHA (해당 Checkout의 실제 값)
- `MACHINE` · `DISTRO` · 활성화한 Fragment 및 Layer 목록
- `conf/local.conf`의 사용자 설정값
- Host OS, 필요한 Host Package 및 사용 가능한 RAM·Disk 자원
- 실제 이미지 빌드와 보드 부팅 결과 (현재 미진행)

설정 자체는 [빌드 설정](build-config.md), 환경 구성·검증 이력은 [Chapter 1](../docs/01-environment.md)을 참조합니다.

## 참고 문서

- [Yocto Project 6.0 — Quick Build](https://docs.yoctoproject.org/6.0/brief-yoctoprojectqs/index.html)
- [Yocto Project 6.0 — Setting Up to Use the Yocto Project](https://docs.yoctoproject.org/6.0/dev-manual/start.html)
