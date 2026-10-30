# Yocto 소스 리비전 관리

센터와 집에서 사용한 Yocto 소스의 Git Commit SHA를 비교한다. **센터 값은 환경 구성 기록**, **집 값은 `git rev-parse HEAD`의 터미널 출력**에 근거한다.

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

| Git Checkout | 센터 기록 SHA | 집에서 확인한 SHA |
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

집에서는 `meta-yocto`와 실제 실행용 BitBake의 SHA까지 확인했다. 센터의 이 두 Checkout SHA는 확보되지 않아 양쪽의 동일성은 확인되지 않았다. 최초 Clone의 Commit을 Setup 내부 BitBake의 SHA로 대체하지 않습니다.

## 4. 재현할 때 함께 비교할 사항

- Remote URL · Branch · Commit SHA (해당 Checkout의 실제 값)
- `MACHINE` · `DISTRO` · 활성화한 Fragment 및 Layer 목록
- `conf/local.conf`의 사용자 설정값
- Host OS, 필요한 Host Package 및 사용 가능한 RAM·Disk 자원
- 이미지 빌드·실장비 검증 결과: **센터** [이미지 빌드](../docs/03-arm64-image-build.md) 및 [Raspberry Pi 4B 부팅](../docs/05-raspberrypi-boot.md) 성공 기록. **집**은 Recipe Parse·메타데이터 분석까지 검증

설정 자체는 [빌드 설정](build-config.md), 환경 구성·검증 이력은 [Chapter 1](../docs/01-environment.md)을 참조합니다.

## 5. 외부 모듈·GPIO 소스 참조 기준

문서 정리 시 두 저장소의 `main`을 조회한 기준(2026-10-29):

| 저장소 | 조회한 HEAD | 용도 |
|---|---|---|
| `yocto-rpi4-lab` | `19a6e8f3b18434a6af17723ded8d1dff7bcf389c` | Chapter·설정·hello-drv 예제를 참조한 당시 문서 기준선 |
| `linux-system-programming` | `56a431d1e633d90f1bfe98a3a7bfaa026494862c` | 직접 개발한 모듈·앱·GPIO 소스의 고정 링크 기준 |

이 절의 SHA는 **참조한 저장소 상태**다. 실제 실장비에서 사용한 모든 바이너리·활성 Overlay가 해당 HEAD에서 생성됐다고 소급하는 값이나 Yocto Git Fetcher의 적용 완료 `SRCREV`가 아니다. 기존 실습은 원본 파일을 Layer의 `files/`로 스테이징했다.

- [Character Driver 모듈 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/yocto-recipe/thermal-core_1.0.bb) · [C 테스트 앱 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/yocto-recipe/thermal-test_1.0.bb)
- [GPIO 모듈 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio_1.0.bb) · [GPIO 앱 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio-test_1.0.bb)
- [8채널 Overlay 템플릿](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/dt/lab-gpio-eight-overlay.dts) · [토글 앱](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/userspace/lab_gpio_test.c)

배포 파일의 동일성은 [SHA-256 검증 로그](../docs/logs/06-module-packaging.md#3-동일한-배포-파일-확인)로 확인한다. 8채널 독립 토글 실장비 확인 기록과 비활성 DT 템플릿의 적용 범위는 [Chapter 7](../docs/07-gpio-toggle-image.md)에 구분해 정리했다.

## 참고 문서

- [Yocto Project 6.0 — Quick Build](https://docs.yoctoproject.org/6.0/brief-yoctoprojectqs/index.html)
- [Yocto Project 6.0 — Setting Up to Use the Yocto Project](https://docs.yoctoproject.org/6.0/dev-manual/start.html)
