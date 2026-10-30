# Chapter 4 — RootFS·Wic 산출물 분석

> **대상:** Raspberry Pi 4B / Yocto 6.0.4 `wrynose` / ARM64
>
> **결과:** Kernel·DTB·RootFS 파일 형식 식별, Wic 압축 검사, MBR 파티션 분석 및 실장비 ext4 루트 마운트 확인

**이 장은 과거 `core-image-minimal`의 분석 기록이다.** 최종 GPIO 이미지의 40,615,730-byte 압축 WIC·4,128 Tasks 결과는 [최종 보고서](final-uart-gpio8-image.md)에서 별도로 추적한다.

## 1. 목표와 분석 환경

빌드 디렉터리의 산출물을 실제 부팅 시스템의 구성 요소에 대응시켰다. 센터 WSL에서 배포 파일과 Wic 파티션을 검사하고 Raspberry Pi UART에서 실행 중인 RootFS를 확인했다. 빌드·부팅 검증 결과를 연결해 분석했으며, 명령과 출력은 Chapter 3·5에 보존했다.

## 2. 배포 산출물을 역할별로 식별

**실행 위치: 센터 WSL / `poky-wrynose/build`**

```bash
ls -lh tmp/deploy/images/raspberrypi4-64/
file -L tmp/deploy/images/raspberrypi4-64/{Image,bcm2711-rpi-4-b.dtb,core-image-minimal-raspberrypi4-64.rootfs.ext3,core-image-minimal-raspberrypi4-64.rootfs.wic.bz2}
```

| 산출물 | 실제 관찰 | 시스템에서의 역할 |
|---|---|---|
| `Image` | ARM64 boot executable, 26M | Linux 커널 |
| `bcm2711-rpi-4-b.dtb` | DTB v17, 56,407 bytes | Pi 4B 하드웨어 기술 |
| `.rootfs.ext3` | ext3 filesystem, 28M | 별도 RootFS 파일시스템 산출물 |
| `.rootfs.tar.bz2` | 5.7M | RootFS 파일 트리 아카이브 |
| `.rootfs.wic.bz2` | bzip2, 29M | 파티션 테이블을 포함한 압축 SD 디스크 이미지 |
| `.rootfs.wic.bmap` | 3.0K | 이미지 기록용 블록 맵 |
| `.rootfs.manifest` | 908 B 파일 존재 | 이미지 설치 패키지 목록 산출물 |
| `modules-*.tgz` | 20M 파일 존재 | 커널 모듈 아카이브 |

파일 크기는 당시 `ls -lh` 표시값이다. `manifest`와 모듈 아카이브는 존재를 확인한 결과이며, 설치된 전체 패키지의 내용 분석 결과로 사용하지 않는다. 파일 시그니처와 전체 산출물 목록은 [Chapter 3 §6–7](03-arm64-image-build.md#6-배포-산출물-확인)에 있다.

## 3. Wic의 부팅 파티션과 RootFS 확인

WSL에서 `bzip2 -t`로 압축 스트림을 검사한 뒤 해제본을 `file`, `fdisk -l`로 분석했다.

| 분석 대상 | 관찰 결과 | 의미 |
|---|---|---|
| 디스크 이미지 | 180,773,888 bytes / 172.4 MiB / DOS·MBR | SD 전체 기록용 이미지 |
| 파티션 1 | 시작 8192 sector, 130 MiB, 타입 `0x0c` | FAT32 부팅 파일 영역 |
| 파티션 2 | 시작 278528 sector, 약 36.4 MiB, 타입 `0x83` | Linux RootFS 영역 |
| 섹터 크기 | 512 bytes | 부팅 영역 offset = 4,194,304 bytes |

부팅 파티션을 `loop,ro,offset=4194304`로 마운트해 `config.txt`와 `cmdline.txt`를 읽었다. 실제 설정에서 `root=/dev/mmcblk0p2 rootfstype=ext4 rootwait`를 확인했다. [분석 명령·출력](05-raspberrypi-boot.md#3-빌드-이미지와-파티션-검증)은 Chapter 5에 있다.

최초 이미지 `20261025055346`을 분석한 뒤, 로그인 Fragment를 적용한 `20261025083110` 이미지로 실장비 로그인을 검증했다. 이미지 식별자와 배포 순서는 [Chapter 5 §6](05-raspberrypi-boot.md#6-root-로그인-허용-및-이미지-재빌드)에서 추적할 수 있다.

## 4. 실행 중인 RootFS와 빌드 설정 연결

**실행 위치: Raspberry Pi UART**

```bash
cat /proc/cmdline
cat /proc/mounts | grep ' / '
df -h /
```

실장비에서 `/dev/root / ext4 rw,relatime`와 파일시스템 크기 `30.5M`, 사용량 `13.7M`를 확인했다. Wic의 약 36.4 MiB 파티션 크기와 `df`의 파일시스템 공간은 서로 다른 값이다. 별도 `.ext3` 산출물의 형식과 Wic으로 부팅한 루트 마운트도 구분한다. [실제 출력](05-raspberrypi-boot.md#72-rootfs-마운트)을 참조한다.

| 빌드 메타데이터에서 확인한 구성 | 실행 결과와의 연결 |
|---|---|
| `IMAGE_INSTALL="packagegroup-core-boot "` | 최소 부팅 패키지를 출발점으로 RootFS 구성 |
| `VIRTUAL-RUNTIME_init_manager="sysvinit"` | 부팅 로그의 `INIT: Entering runlevel: 5` |
| BusyBox 기본 도구·로그인 | Target 기본 셸 명령과 `udhcpc` 실행 |
| `VIRTUAL-RUNTIME_dev_manager="udev"` | 사용자 공간 장치 관리 선택. 이것만으로 특정 모듈의 `/dev` 생성·probe 성공을 입증하지 않음 |
| `WKS_FILE="sdimage-raspberrypi.wks"` | 실제 Wic의 부팅 영역·RootFS 파티션 검사 |

메타데이터 원문은 [Chapter 2 §6–8](02-bitbake-layer-recipe.md#6-image-recipe와-runtime-packagegroup), 실행 근거는 [Chapter 5](05-raspberrypi-boot.md)에 있다. 이 대응은 설정과 관찰 결과의 연결이며 Manifest 전체를 역추적한 결과는 아니다.

## 5. 시스템 통합에 적용한 판단

이미지 생성은 파일시스템 하나를 만드는 작업을 넘어 커널·DTB·부팅 설정·RootFS를 조합하는 과정이다. 외부 `.ko`가 빌드되거나 `modules-*.tgz`가 생성돼도 해당 모듈이 RootFS에 설치되는 것은 별도 선택이다. 실제 `hello_drv.ko`는 파일 전송 후 수동 적재로 검증했다.

이 구분을 바탕으로 [Chapter 6](06-custom-layer.md)에서는 모듈·앱의 Recipe 빌드를, [Chapter 7](07-gpio-toggle-image.md)에서는 GPIO 패키지·Overlay·부팅 서비스의 통합 지점을 설명한다.

## 6. 기본 이미지 분석에서 최종 WIC 검사로 확장

`VIRTUAL-RUNTIME_dev_manager=udev`는 사용자 공간 관리자의 선택이다. 특정 GPIO 장치가 존재하는지는
DT 노드의 활성화, platform matching/probe, 드라이버의 장치 등록, devtmpfs/udev 처리를 구분해 확인해야 한다.
직접 개발한 GPIO Driver는 probe에서 misc 장치를 등록한다. [소스](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/driver/lab_gpio.c)와
[최종 HW 관측](logs/07-gpio-image-hardware-20261030.md)을 통해 노드 8개 확인과 bind 원문 미확보를 구별했다.

최종 WIC는 MBR의 boot/root 영역을 읽기 전용 도구로 검사했다. FAT에서 config/cmdline/DTBO를 추출하고,
RootFS에서 실행 파일·모듈·init symlink·getty·인증 정책을 검사했다. 파일이 deploy 디렉터리에 있는 것과
완성 이미지 안에 들어 있는 것을 별도로 확인한 절차는 [최종 보고서](final-uart-gpio8-image.md#host-증거)에 있다.
기본 이미지의 파티션/파일시스템 크기와 최종 이미지의 압축 크기를 비교할 때 단위를 혼동하지 않는다.
