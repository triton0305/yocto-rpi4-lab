# Yocto 빌드 설정

이 문서는 환경 구성 명령을 중복 나열하지 않고, **설정의 출처·의미·적용값·점검 방법**을 정리합니다. 실제 진행 순서 및 과거 검증 기록은 [Chapter 1](../docs/01-environment.md)을 참조합니다.

## 1. 현재 기록된 설정

| 변수 또는 구성 | 현재 기록된 값 | 설정 출처 |
|---|---|---|
| Yocto Project | 6.0.4 (wrynose) | `bitbake-setup`으로 구성한 Setup |
| `DISTRO` | `poky` | 초기 Setup의 Distribution 선택(`distro/poky`) |
| `MACHINE` | `raspberrypi4-64` | `machine/raspberrypi4-64` Fragment 활성화 |
| BSP Layer | `meta-raspberrypi` | `bitbake-layers add-layer` |
| `BB_NUMBER_THREADS` | `4` | `build/conf/local.conf` |
| `PARALLEL_MAKE` | `-j 4` | `build/conf/local.conf` |

Host는 WSL2 Ubuntu(x86-64), Target은 Raspberry Pi 4B(ARM64)입니다. 기존 실습 기록상 WSL2 RAM은 15GiB이고 논리 CPU는 24개입니다. 이 Host 수치는 이번 문서 수정에서 새로 측정한 값이 아닙니다.

## 2. Target Machine과 Configuration Fragment

초기 `qemuarm64` 구성에서 Raspberry Pi 4B용으로 변경할 때 다음 명령을 사용했습니다.

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

- `enable-fragment`: Fragment를 활성화하여 해당 설정을 BitBake 환경에 적용합니다.
- Yocto 6.0에서는 활성화한 Fragment 이름을 `build/conf/toolcfg.conf`의 `OE_FRAGMENTS`에 자동 반영합니다.
- `DISTRO=poky`는 기존 Setup 초기 선택 기록입니다. `toolcfg.conf`의 현재 전체 내용까지 GitHub에서 직접 확인한 것은 아닙니다.

설정 확인용 명령(이번 문서 정비에서 재실행하지 않음):

```bash
bitbake-config-build list-fragments
bitbake -e | grep -E '^(MACHINE|DISTRO)='
```

`list-fragments`는 사용 가능·활성화 상태의 Fragment를 살펴보고, `bitbake -e`는 최종 BitBake 변수 값을 조회합니다.

## 3. 병렬 빌드 제한

`build/conf/local.conf`의 기존 기록:

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

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

기존 실습 기록에서는 `MACHINE=raspberrypi4-64`, `DISTRO=poky`, 병렬도 값의 적용, `raspberrypi` Layer Priority 9를 확인했습니다. 이번 수정에서는 WSL을 직접 실행하거나 검증값을 새로 측정하지 않았습니다.

## 5. 이미지 빌드 상태

- [x] Build Environment 및 BSP Layer 구성 (기존 기록)
- [x] Target Machine·병렬도 설정 확인 (기존 기록)
- [ ] `core-image-minimal` 이미지 빌드
- [ ] Raspberry Pi 4B에서 이미지 부팅 확인

외부 Source Checkout 버전은 [소스 리비전](source-revisions.md) 문서에서 별도로 관리합니다.

## 참고 문서

- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
- [Yocto Project 6.0 — Variables Glossary](https://docs.yoctoproject.org/6.0/ref-manual/variables.html)
