# Yocto 빌드 설정

이 문서는 환경 구성 명령을 중복 나열하지 않고, **설정의 출처·의미·적용값·점검 방법**을 정리합니다. 실제 진행 순서 및 과거 검증 기록은 [Chapter 1](../docs/01-environment.md)을 참조합니다.

## 1. 센터·집 설정 비교

설정은 **개발 Host별로 다르게 적용**했습니다. 두 Host를 동일한 `local.conf` 설정으로 취급하지 않습니다. 아래 값은 센터의 기존 문서 및 집 노트북의 사용자 제공 검증 결과를 기준으로 합니다.

| 항목 | 센터(학교) | 집 노트북 |
|---|---|---|
| Host | WSL2 Ubuntu (x86-64) | WSL2 Ubuntu 26.04.1 LTS (x86-64) |
| WSL2 RAM | 15GiB | 7.6GiB |
| 논리 CPU | 24개(기존 기록) | 미확인 |
| Yocto | 6.0.4 (wrynose) | 6.0.4 (wrynose) |
| `DISTRO` | `poky` | `poky` |
| `MACHINE` | `raspberrypi4-64` | `raspberrypi4-64` |
| BSP Layer | `meta-raspberrypi` | `meta-raspberrypi` |
| `BB_NUMBER_THREADS` | `4` | `2` |
| `PARALLEL_MAKE` | `-j 4` | `-j 2` |
| `bitbake -p` | 별도 기록 없음 | 성공: 992 `.bb`, 0 errors, Exit 0 |

설정 출처는 초기 `bitbake-setup`에서 선택한 `poky`, 활성화한 `machine/raspberrypi4-64` Fragment, BSP Layer 등록, 각 Host의 `build/conf/local.conf`입니다. 이번 문서 정비에서 실제 Host 구성 파일을 직접 대조한 것은 아닙니다.

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

## 3. Host별 병렬 빌드 제한

**센터의 `build/conf/local.conf` (기존 수행 기록)**

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

**집 노트북의 `build/conf/local.conf` (사용자 제공 설정 기록)**

```conf
BB_NUMBER_THREADS = "2"
PARALLEL_MAKE = "-j 2"
```

집 노트북은 보고된 RAM 7.6GiB를 고려해 센터보다 병렬도를 낮췄습니다. 이는 자원 사용을 줄이기 위한 설정이며, 전체 이미지 빌드 성공 여부나 필요 자원 충족을 증명하지 않습니다.

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

센터 기존 실습 기록에서는 `MACHINE=raspberrypi4-64`, `DISTRO=poky`, 센터의 병렬도 값 적용 및 `raspberrypi` Layer Priority 9를 확인했습니다. 집 노트북은 설정 완료와 `bitbake -p` 정상 종료가 보고되었습니다. 이는 집에서 `bitbake -e`의 각 변수 출력을 새로 확보했다는 뜻은 아닙니다. 이번 문서 수정에서 WSL을 직접 실행하거나 검증값을 새로 측정하지 않았습니다.

## 5. 이미지 빌드 상태

- [x] Build Environment 및 BSP Layer 구성 (기존 기록)
- [x] Target Machine·병렬도 설정 확인 (센터의 기존 기록)
- [x] 집 노트북 `bitbake -p` Parse 정상 종료 (사용자 제공 결과)
- [ ] `core-image-minimal` 이미지 빌드
- [ ] Raspberry Pi 4B에서 이미지 부팅 확인

외부 Source Checkout 버전은 [소스 리비전](source-revisions.md) 문서에서 별도로 관리합니다.

## 참고 문서

- [Yocto Project 6.0 — Configuration Fragments](https://docs.yoctoproject.org/6.0/ref-manual/fragments.html)
- [Yocto Project 6.0 — Variables Glossary](https://docs.yoctoproject.org/6.0/ref-manual/variables.html)
