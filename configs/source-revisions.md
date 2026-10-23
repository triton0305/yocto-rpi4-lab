# Yocto 소스 리비전 관리

학교와 집에서 Yocto 개발 환경의 버전을 비교·재현하기 위해 외부 Source의 Commit SHA를 관리합니다. **센터 값은 기존 실습 기록**, **집 값은 사용자가 제공한 `git rev-parse HEAD` 실제 출력**에 근거합니다. GitHub 문서 수정 과정에서 WSL에 직접 접속하거나 Checkout을 재조회하지 않았습니다.

## 1. 기본 구성

| 항목 | 기록 |
|---|---|
| Yocto Project | 6.0.4 (wrynose) |
| DISTRO | `poky` |
| MACHINE | `raspberrypi4-64` |
| Host / Target | WSL2 Ubuntu (x86-64) / Raspberry Pi 4B (ARM64) |
| 환경 구성 방식 | `bitbake-setup init` (`poky-wrynose` 선택 기록) |

## 2. Source Checkout 비교 (센터 기록 / 집 실행 로그)

**주의:** 최초 `bitbake-setup` 호출을 위해 독립적으로 Clone한 BitBake와 **실제 Setup이 사용하는 `layers/bitbake`는 별도 Git Checkout**입니다. 각각의 SHA가 서로 다른 것은 이 기록만으로 오류가 아닙니다.

| Git Checkout | 센터 기록 SHA | 집 노트북 실제 확인 SHA |
|---|---|---|
| 최상위 초기화용 BitBake | `3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e` | **동일** |
| Setup 내부 `layers/bitbake` (실행용) | **미확인** | `6e260eb6ab1631607ea414d9ff8ede1155faa5d9` |
| `layers/openembedded-core` | `636e5d3b12d54951c13d57346648bc29a0e6b24e` | **동일** |
| `layers/meta-yocto` | **미확인** | `7c25b11156553145fa6b241a2d4f65d94438f804` |
| `layers/meta-raspberrypi` | `919588393f41b48cb6c5d832aa35e58a19b6762d` | **동일** |

집의 각 SHA는 [집 실행 로그 — Checkout SHA](../docs/logs/01-home-setup.md#10-각-git-checkout의-sha--실행-로그)의 `git rev-parse HEAD` 결과에 근거합니다. 센터는 [센터 실행 근거](../docs/logs/01-center-setup.md)에 기록된 결과이며, 실제 출력 전문이 없는 값은 **기록 기반**입니다.

**확인된 동등성:** 두 환경의 초기화용 BitBake, OpenEmbedded-Core, meta-raspberrypi에 관한 기록 SHA는 일치합니다. **확인되지 않은 동등성:** 실행용 BitBake와 meta-yocto의 센터 SHA는 미확보입니다. 따라서 양쪽 Build Environment 전체 소스가 동일하다고 주장하지 않습니다.

Commit SHA만으로 Host 패키지, 가용 자원 또는 변경된 설정이 동일하다고 단정할 수 없습니다. 재현 시 Remote URL, Branch, Git HEAD, Layer 및 최종 BitBake 환경 변수를 함께 확인해야 합니다.

## 3. 재현 시 로컬 Checkout 대조 명령

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

이 상대 경로는 집의 `poky-wrynose/build` 구조와 실제 기록으로 확인됐습니다. 센터에서는 실제 Checkout 위치를 먼저 확인한 후 사용해야 합니다.

집에서는 `meta-yocto`와 실제 실행용 BitBake의 SHA까지 확인했습니다. **센터는 이 두 Checkout의 SHA가 미확보**이므로 센터의 해당 Git 저장소 루트에서 `git rev-parse HEAD`를 별도로 실행해야 학교·집 동일성을 판단할 수 있습니다. 최초 Clone의 Commit을 Setup 내부 BitBake의 SHA로 대체하지 않습니다.

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
