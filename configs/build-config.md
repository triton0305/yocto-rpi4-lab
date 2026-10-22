# Yocto 빌드 설정

## 1. 빌드 환경

| 항목 | 설정 |
|---|---|
| Yocto | 6.0.4 (wrynose) |
| Distribution | poky |
| Machine | raspberrypi4-64 |
| BSP Layer | meta-raspberrypi |
| Host | WSL2 Ubuntu (x86-64) |

## 2. Target 설정

초기에는 `qemuarm64`로 환경을 구성한 뒤, Raspberry Pi 4B용 BSP Layer를 등록하고 빌드 대상을 변경했다.

```bash
bitbake-config-build enable-fragment machine/raspberrypi4-64
```

설정 확인 결과:

```text
MACHINE="raspberrypi4-64"
DISTRO="poky"
```

## 3. 병렬 빌드 설정

WSL2에 할당된 메모리는 15GiB이며, 사용 가능한 논리 CPU는 24개다.

과도한 병렬 빌드로 인한 메모리 부족을 방지하기 위해 `conf/local.conf`에 다음 설정을 적용했다.

```conf
BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

- `BB_NUMBER_THREADS`: BitBake의 동시 작업 수 제한
- `PARALLEL_MAKE`: Make 기반 컴파일의 병렬 작업 수 제한

## 4. 설정 검증

```bash
bitbake -e | grep -E '^(MACHINE|DISTRO|BB_NUMBER_THREADS|PARALLEL_MAKE)='
```

설정 변경 시 실제 적용된 값을 확인한다.

## 5. 빌드 상태

- [x] Yocto 환경 구성
- [x] Raspberry Pi BSP 등록
- [x] Target Machine 설정
- [x] 병렬도 제한 설정
- [ ] core-image-minimal 빌드
- [ ] Raspberry Pi 실장비 부팅 검증

