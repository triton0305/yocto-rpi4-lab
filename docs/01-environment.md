# Chapter 1 — Yocto 개발 환경 구성

## 1. 목표

WSL2 Ubuntu 환경에서 Yocto Project 빌드 시스템을 구성하고, Raspberry Pi 4B용 ARM64 Linux 이미지를 생성하기 위한 개발 환경을 준비한다.

## 2. 개발 환경

| 항목 | 구성 |
|---|---|
| Host | WSL2 Ubuntu (x86-64) |
| Target | Raspberry Pi 4 Model B |
| Yocto | 6.0.4 (wrynose) |
| Distribution | Poky |
| Machine | raspberrypi4-64 |
| BSP Layer | meta-raspberrypi |

## 3. BitBake 설치 및 환경 초기화

BitBake 소스를 다운로드하고 Yocto 6.0 빌드 환경을 구성했다.

```bash
cd ~/study/rootfs/yocto

git clone https://git.openembedded.org/bitbake

./bitbake/bin/bitbake-setup init
```

초기 설정에서 다음 항목을 선택했다.

- Configuration: `poky-wrynose`
- BitBake Configuration: `poky`
- Target Machine: `qemuarm64` (초기 설정)
- Distribution: `poky`

초기 설정 이후 Raspberry Pi 4B를 대상으로 변경했다.

## 4. Locale 오류 해결

BitBake 서버 시작 과정에서 다음 오류가 발생했다.

```text
Please make sure locale 'en_US.UTF-8' is available on your system
```

Ubuntu에 필요한 Locale을 생성하여 해결했다.

```bash
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
```

`locale -a` 명령으로 `en_US.utf8`이 생성된 것을 확인했다.

## 5. Raspberry Pi BSP Layer 등록

Raspberry Pi 하드웨어 지원을 위해 `meta-raspberrypi` Layer를 추가했다.

```bash
git clone -b wrynose \
  https://git.yoctoproject.org/meta-raspberrypi \
  ../layers/meta-raspberrypi

bitbake-layers add-layer ../layers/meta-raspberrypi
```

다음 명령으로 등록 여부를 확인했다.

```bash
bitbake-layers show-layers
```

출력에서 `raspberrypi` Layer와 Priority 9를 확인했다.

## 6. Target Machine 변경

빌드 대상을 QEMU ARM64에서 Raspberry Pi 4B ARM64로 변경했다.

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

BitBake 환경 변수 확인 결과:

```text
DISTRO="poky"
DISTRO_VERSION="6.0.4"
MACHINE="raspberrypi4-64"
MACHINE_ARCH="raspberrypi4_64"
```

## 7. 빌드 병렬도 제한

WSL2에 할당된 RAM이 15GiB이므로 빌드 중 메모리 부족 가능성을 줄이기 위해 병렬도를 제한했다.

`conf/local.conf`:

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

`bitbake -e`로 두 설정이 적용된 것을 확인했다.

## 8. 결과

- [x] BitBake 개발 환경 초기화
- [x] Locale 오류 해결
- [x] Raspberry Pi BSP Layer 등록
- [x] ARM64 MACHINE 설정 적용
- [x] 빌드 병렬도 설정 및 확인
- [ ] Linux 이미지 빌드
- [ ] Raspberry Pi 4B 부팅 검증

Chapter 1 환경 구성 완료.

이미지 빌드 및 실장비 검증은 후속 Chapter에서 진행한다.

