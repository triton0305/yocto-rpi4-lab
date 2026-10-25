# Chapter 5 — Raspberry Pi 4B Yocto 실장비 부팅·검증

> **실습일:** 2026-10-25  
> **목적:** ARM64 Linux 이미지의 SD 카드 기록부터 UART 로그인·RootFS·네트워크 검증까지 진행하고, 외부 커널 모듈의 빌드·전송·삽입·제거를 실제 장비에서 확인한다.  
> **결과:** 부팅 성공 / root 로그인 성공 / Ethernet 통신 성공 / 외부 커널 모듈 `hello_drv.ko` 삽입·제거 성공  

> [!IMPORTANT]
> 이 문서는 당시 **실제로 실행한 명령과 확인된 출력**을 기준으로 작성했다. `실제 출력` 블록은 당시 기록의 발췌이며, IP 주소·시간·이미지 타임스탬프·디스크 번호 등은 다시 실행하면 달라질 수 있다. 파일이 생성됐다는 사실과 실장비에서 동작했다는 사실을 구분해서 기록한다.
>
> **환경 참고:** IP 주소·계정명·장치 경로는 당시 실습 환경의 값이며 다른 환경에서 그대로 적용되는 값은 아니다. 실제 비밀번호나 인증 비밀은 기재하지 않았다.

## 핵심 결과 요약

| 검증 단계 | 확인한 결과 | 증거 위치 |
|---|---|---|
| 이미지 및 매체 | Wic 파티션 구조 확인, SD 대상 디스크 식별 후 기록 | §3–4 |
| 실제 부팅 | Raspberry Pi 4B에서 UART 콘솔 진입 및 root 로그인 | §5–6 |
| 시스템 | Linux `6.18.33-v8`, AArch64 커널, ext4 RootFS | §7 |
| 네트워크 | Ethernet 1 Gbps, DHCP IPv4, 외부 IP ping 4/4 | §8 |
| 설정 변경·재빌드 | root 로그인용 개발 Fragment 적용 후 증분 재빌드 | §6 |
| 외부 커널 모듈 | `hello_drv.ko` ARM64 빌드, HTTP 전송, `insmod`/`rmmod`, `dmesg` | §10 |

**문제 해결의 핵심:** 최초 이미지에서는 로그인 프롬프트까지 부팅됐지만 root 로그인이 되지 않았다. 개발용 로그인 정책을 명시적으로 적용해 이미지를 다시 빌드했고, 이후 실제 장비에서 로그인을 확인했다. 외부 커널 모듈은 이미지를 다시 기록하지 않고도 별도로 빌드·전송·로드할 수 있음을 검증했다.

**모듈 검증 범위:** `hello_drv.ko`는 Yocto Recipe로 빌드해 파일로 전송하고 수동 적재했다. 이미지에 자동 포함하거나 GPIO 제어를 구현한 결과는 아니다. 최초 이미지 빌드 로그는 [ARM64 이미지 빌드 기록](03-arm64-image-build.md)을 참조한다.

**검증 환경:** 센터 WSL2 Ubuntu 22.04에서 빌드한 이미지를 Raspberry Pi 4B에서 검증했다. 환경 구성과 메타데이터 분석은 [Chapter 1](01-environment.md)·[Chapter 2](02-bitbake-layer-recipe.md)에 기록했다.

**추가 확인이 필요한 부분:** 실제 부팅 체인에서 U-Boot 사용 여부와 펌웨어→커널 연결은 이 문서의 로그만으로 확정하지 않는다. 부팅 파티션에 관련 파일이 존재하는 사실과 실제 실행 여부는 구별한다.

> **개발 환경 보안:** 비밀번호 없는 root 로그인 허용 Fragment와 `0.0.0.0`에 바인딩한 임시 HTTP 서버는 통제된 실습 환경에서만 사용했다. 실제 배포용 이미지에서는 로그인 정책을 재설계하고 임시 파일 서버를 종료해야 한다.

---

## 목차

1. [실습 환경과 경로](#1-실습-환경과-경로)
2. [전체 진행 흐름](#2-전체-진행-흐름)
3. [빌드 이미지와 파티션 검증](#3-빌드-이미지와-파티션-검증)
4. [SD 카드 장치 식별 및 기록](#4-sd-카드-장치-식별-및-기록)
5. [UART 콘솔 설정과 첫 부팅](#5-uart-콘솔-설정과-첫-부팅)
6. [root 로그인 허용 및 이미지 재빌드](#6-root-로그인-허용-및-이미지-재빌드)
7. [실장비 시스템·RootFS 검증](#7-실장비-시스템rootfs-검증)
8. [Ethernet·DHCP·외부 통신 검증](#8-ethernetdhcp외부-통신-검증)
9. [root 비밀번호 변경 및 재부팅](#9-root-비밀번호-변경-및-재부팅)
10. [외부 커널 모듈 빌드와 동작 검증](#10-외부-커널-모듈-빌드와-동작-검증)
11. [문제·원인·해결 기록](#11-문제원인해결-기록)
12. [검증 결과와 미해결 항목](#12-검증-결과와-미해결-항목)

---

## 1. 실습 환경과 경로

### 하드웨어 / 소프트웨어

| 분류 | 구성 |
|---|---|
| Host | Windows + WSL2 Ubuntu 22.04 (`kccistc`) |
| Target | Raspberry Pi 4 Model B, 64-bit ARM |
| Yocto | Poky 6.0.4, `wrynose` |
| 머신 설정 | `MACHINE=raspberrypi4-64` |
| 타깃 트리플 | `aarch64-poky-linux` |
| 타깃 커널 | `6.18.33-v8` |
| BSP | `meta-raspberrypi` |
| 이미지 | `core-image-minimal` |
| SD 카드 | 128 GB USB 카드 리더기 사용 |
| 콘솔 | USB–UART 3.3V, Windows COM9, 115200 baud, 8N1 |
| 파일 전송 | Windows 임시 HTTP 서버 → Target `wget` |

### 명령 실행 환경 구분

이 문서에서는 명령 실행 위치를 다음처럼 표기한다. **서로 다른 환경의 경로를 혼용하면 파일을 찾을 수 없다.**

| 표기 | 프롬프트 예시 | 실제 역할 |
|---|---|---|
| **WSL** | `kccistc@DESKTOP-...:...$` | BitBake, 커널 모듈 크로스 컴파일, 이미지 검사 |
| **Windows PowerShell** | `PS C:\...>` | SD 카드 검색, Raspberry Pi Imager, miniterm, HTTP 서버 |
| **Target (UART)** | `root@raspberrypi4-64:~#` | 실제 Pi에서 Linux 명령, 모듈 삽입·제거 |

주요 경로는 다음과 같다.

```text
# WSL: Yocto 빌드 루트
/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build

# WSL: 빌드 산출물
.../build/tmp/deploy/images/raspberrypi4-64/

# WSL: SD 기록용으로 압축 해제한 이미지
/home/kccistc/study/rootfs/yocto/image-inspection/rpi4-root-login.img

# Windows 탐색기에서 WSL 파일 직접 접근
\\wsl.localhost\Ubuntu-22.04\home\kccistc\study\rootfs\yocto\image-inspection\rpi4-root-login.img

# 실제 SD 카드 FAT 부팅 파티션 (실습 당시)
E:\config.txt
E:\cmdline.txt
```

WSL에서 Yocto 환경을 준비할 때는 아래처럼 실행한다.

**실행 위치: WSL / 시작 경로: `~/study/rootfs/yocto`**

```bash
cd ~/study/rootfs/yocto
source bitbake-builds/poky-wrynose/build/init-build-env
pwd
```

**기대:** 현재 위치가 `.../poky-wrynose/build`로 변경된다. `bitbake` 관련 명령은 이 환경에서 수행한다.

---

## 2. 전체 진행 흐름

```text
WSL2 / Yocto
  ├─ core-image-minimal 빌드 (Chapter 3에서 완료)
  ├─ .wic.bz2 → .wic/.img 압축 해제
  └─ MBR · 파티션 검사
                  │
                  ▼
Windows / Raspberry Pi Imager
  ├─ 128 GB SD 카드 식별
  ├─ 이미지 기록·검증
  └─ SD Boot 파티션에 UART 설정
                  │
                  ▼
Raspberry Pi 4B / UART
  ├─ Poky 로그인 프롬프트 확인
  ├─ root 로그인 정책 수정 후 재빌드·재기록
  ├─ root 로그인 / ARM64 / Kernel / RootFS 검증
  └─ eth0 · DHCP · ping 성공
                  │
                  ▼
추가 실습 (Chapter 8 선행)
  ├─ WSL에서 hello_drv.ko 크로스 컴파일
  ├─ LAN / HTTP로 .ko 전송
  └─ Pi에서 insmod → dmesg → rmmod 성공
```

> **중요한 구분:** SD 카드에 OS 이미지를 기록하는 작업과, 실행 중인 Linux에 개별 `.ko` 파일을 전달해 로드하는 작업은 다르다. 후자는 반드시 이미지 전체를 다시 기록해야 하는 작업이 아니다.

---

## 3. 빌드 이미지와 파티션 검증

### 3.1 이미지 산출물 확인

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
ls -lh tmp/deploy/images/raspberrypi4-64/
```

**실제 출력에서 확인한 주요 파일:**

```text
core-image-minimal-raspberrypi4-64.rootfs-20261025055346.wic.bz2   29M
core-image-minimal-raspberrypi4-64.rootfs-20261025055346.ext3       28M
core-image-minimal-raspberrypi4-64.rootfs-20261025055346.tar.bz2    5.7M
core-image-minimal-raspberrypi4-64.rootfs-20261025055346.wic.bmap   3.0K
Image-1-6.18.33+git0+...bin                                          26M
bcm2711-rpi-4-b.dtb                                                 56K
```

파일 용도:

- `.wic.bz2`: **디스크 전체 이미지**를 bzip2로 압축한 파일. 파티션 테이블까지 포함하므로 SD 카드 기록 대상이다.
- `.ext3`: RootFS 파일시스템 산출물. 단독으로 SD 전체를 기록하는 파일과 혼동하지 않는다.
- `.tar.bz2`: RootFS 파일 트리 아카이브. 파일 분석·배포 등에 활용한다.
- `.wic.bmap`: 블록 맵. 이를 지원하는 기록 도구에서 활용할 수 있다.
- `Image`: ARM64 커널 이미지.
- `bcm2711-rpi-4-b.dtb`: Raspberry Pi 4B의 Device Tree Blob.

> 목록에 다양한 `.dtbo`가 있다고 해서 전부 부팅 시 적용되는 것은 아니다. 실제 활성화된 Overlay는 부팅 파티션의 `config.txt`에서 확인한다.

### 3.2 WIC 압축 확인 및 해제

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
DEPLOY=tmp/deploy/images/raspberrypi4-64
IMG="$DEPLOY/core-image-minimal-raspberrypi4-64.rootfs.wic.bz2"

mkdir -p ~/study/rootfs/yocto/image-inspection
bzip2 -t "$IMG" &&
  bzip2 -dc "$IMG" > ~/study/rootfs/yocto/image-inspection/core-image-minimal.wic

file ~/study/rootfs/yocto/image-inspection/core-image-minimal.wic
fdisk -l ~/study/rootfs/yocto/image-inspection/core-image-minimal.wic
```

**실제 출력:**

```text
.../core-image-minimal.wic: DOS/MBR boot sector; partition 1 : ID=0xc;
partition 2 : ID=0x83

Disk .../core-image-minimal.wic: 172.4 MiB, 180773888 bytes, 353074 sectors
Sector size (logical/physical): 512 bytes / 512 bytes
Disklabel type: dos

Device                     Boot  Start    End Sectors   Size Id Type
...core-image-minimal.wic1    *    8192 274431  266240   130M  c W95 FAT32 (LBA)
...core-image-minimal.wic2       278528 353073   74546  36.4M 83 Linux
```

**해석:**

| 구분 | 파티션 1 | 파티션 2 |
|---|---|---|
| 역할 | 부팅 파일·커널·DTB | Linux RootFS |
| 크기 | 130 MiB | 약 36.4 MiB |
| MBR 파티션 타입 | `0x0c` (FAT32 LBA) | `0x83` (Linux) |
| 시작 섹터 | 8192 | 278528 |
| 시작 바이트 오프셋 | `8192 × 512 = 4194304` | `278528 × 512 = 142606336` |

SD 카드가 128GB라도 현재 만들어진 디스크 이미지의 파티션 합계는 약 166.4MiB이고, 나머지 공간은 자동으로 RootFS에 확장되지 않는다.

### 3.3 이미지 안의 실제 부팅 설정 읽기

**실행 위치: WSL / 작업 경로: 무관**

```bash
IMG=~/study/rootfs/yocto/image-inspection/core-image-minimal.wic
sudo mkdir -p /mnt/yocto-boot
sudo mount -t vfat -o loop,ro,offset=4194304 "$IMG" /mnt/yocto-boot

cat /mnt/yocto-boot/config.txt
cat /mnt/yocto-boot/cmdline.txt

sudo umount /mnt/yocto-boot
```

**실제 출력 중 중요한 부분:**

```ini
# Enable VC4 Graphics
dtoverlay=vc4-kms-v3d
```

```text
dwc_otg.lpm_enable=0 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait net.ifnames=0
```

`config.txt`에서 `#`로 시작하는 설정은 주석이므로 활성화되지 않는다. 당시에는 공식 DSI LCD용 `vc4-kms-dsi-7inch` Overlay가 **명시적으로** 활성화되어 있지 않았다. LCD 화면이 잠깐 나오다가 사라지는 문제가 있었지만, **최종 원인을 확정하지는 않았다.** 실장비 부팅 진단은 UART로 진행했다.

> **주의:** `/mnt/yocto-boot`는 WSL 안의 `.wic` 파일을 읽기 전용으로 마운트한 경로다. 이 경로에서 수정한다고 실제 SD 카드에 자동 반영되지 않는다.

---

## 4. SD 카드 장치 식별 및 기록

### 4.1 디스크 번호 대조

**실행 위치: Windows PowerShell / 작업 경로: 무관**

SD 카드 연결 **전·후에 각각** 실행한다.

```powershell
Get-Disk | Format-Table Number,FriendlyName,BusType,Size,PartitionStyle
```

**실제 출력(연결 전):**

```text
Number FriendlyName                 BusType   Size          PartitionStyle
     1 SAMSUNG MZVL21T0HCLR-00B00   NVMe     1024209543168 GPT
     0 PNY CS900 500GB SSD          SATA      500107862016 GPT
```

**실제 출력(연결 후):**

```text
Number FriendlyName                 BusType   Size          PartitionStyle
     1 SAMSUNG MZVL21T0HCLR-00B00   NVMe     1024209543168 GPT
     0 PNY CS900 500GB SSD          SATA      500107862016 GPT
     2 Generic STORAGE DEVICE       USB       127999672320 MBR
```

따라서 당시 새로 나타난 **Disk 2 / Generic STORAGE DEVICE / 약 128GB**가 SD 카드 리더기로 식별됐다. 다시 연결할 때는 디스크 번호가 바뀔 수 있으므로 **현재 목록과 실제 카드 용량을 재확인**한다. 시스템 SSD를 기록 대상으로 선택하면 데이터가 삭제될 수 있다.

**SD 카드 부팅 파티션 드라이브 문자 확인** (실습 당시 Disk 2):

```powershell
Get-Partition -DiskNumber 2 | Get-Volume |
  Format-Table DriveLetter,FileSystem,Size
```

**실제 출력:**

```text
DriveLetter FileSystem      Size
E           FAT        136155136
```

당시 부팅 파티션은 `E:`였으며 크기 약 130MiB로 WIC 파티션 1과 일치했다. Windows 출력의 `FAT` 표기와 `fdisk`의 파티션 타입 `0x0c`는 서로 다른 관찰 항목이다.

### 4.2 Raspberry Pi Imager로 기록

**실행 위치: Windows / GUI: Raspberry Pi Imager**

1. 장치: **Raspberry Pi 4**.
2. OS: **Use Custom / 사용자 지정 이미지**.
3. 이미지: WSL의 `.wic`를 압축 해제한 `.img` 파일.
4. 저장장치: 새로 연결된 **Generic STORAGE DEVICE (128GB)**인지 재확인.
5. **쓰기 및 검증** 완료 후 안전하게 제거.

Windows 탐색기/Imager에서 WSL 파일을 직접 선택할 수 있었다. 따라서 **Windows Downloads 폴더로 별도 복사할 필요는 없다.**

```text
\\wsl.localhost\Ubuntu-22.04\home\kccistc\study\rootfs\yocto\image-inspection\rpi4-root-login.img
```

> 실습 중 한 차례 Downloads 폴더로 복사하는 방법도 시도했지만, 최종적으로는 WSL 파일 직접 선택이 가능함을 확인했다. `explorer.exe <WSL 경로>`는 **탐색기를 열 뿐 파일을 내보내거나 복사하지 않는다.**

---

## 5. UART 콘솔 설정과 첫 부팅

### 5.1 장비 연결

- Raspberry Pi 4B에 SD 카드 장착.
- USB–UART 변환기를 **3.3V 로직**의 TX/RX/GND에 연결. 5V를 UART 신호 핀에 연결하지 않는다.
- 일반적인 GPIO 확장 보드가 헤더 핀을 그대로 연장하는 형태라면 별도 소프트웨어 설정은 필요하지 않다. 다만 **핀 배치와 다른 장치의 중복 점유는 확인**해야 한다.

| Pi 40핀 헤더 | UART 역할 | USB–UART 변환기 |
|---|---|---|
| 물리 핀 8 / GPIO14 | TX | RX |
| 물리 핀 10 / GPIO15 | RX | TX |
| 물리 핀 6 | GND | GND |

이번 장비에는 DSI 방식 LCD도 연결되어 있었지만(정확한 모듈 규격은 별도 확인 필요), 처음에는 부팅 로그가 잠깐 보이다가 화면 출력이 사라졌다. 따라서 디스플레이와 무관하게 검증 가능한 **UART를 기준 콘솔**로 선택했다.

### 5.2 SD 카드의 UART 설정

**실행 위치: Windows PowerShell / SD 카드의 FAT 부팅 파티션(실습 당시 `E:`)**

```powershell
notepad E:\config.txt
notepad E:\cmdline.txt
```

`E:\config.txt` 마지막 부분:

```ini
#dtoverlay=act-led,activelow=off
# Enable VC4 Graphics
dtoverlay=vc4-kms-v3d

# Enable UART
enable_uart=1
```

`E:\cmdline.txt`: **기존 값을 유지한 채 한 줄 끝에 `console=serial0,115200` 추가**

```text
dwc_otg.lpm_enable=0 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait net.ifnames=0 console=serial0,115200
```

> `cmdline.txt`는 반드시 **한 줄**로 작성한다. `root=/dev/mmcblk0p2`는 SD 카드 두 번째 파티션을 RootFS로 사용한다는 의미다. 실제 부팅에서는 `serial0`가 `/dev/ttyS0` 콘솔로 연결됐다.

**저장 여부 검증 명령** (실제 실행 위치: Windows PowerShell):

```powershell
Get-Content E:\config.txt | Select-Object -Last 8
Get-Content E:\cmdline.txt
```

**실제 출력:**

```text
#dtoverlay=act-led,activelow=off
# Enable VC4 Graphics
dtoverlay=vc4-kms-v3d

# Enable UART
enable_uart=1

dwc_otg.lpm_enable=0 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait  net.ifnames=0 console=serial0,115200
```

### 5.3 Windows miniterm 연결 및 첫 로그인

**실행 위치: Windows PowerShell / 작업 경로: 무관**

```powershell
Python -m serial.tools.miniterm COM9 115200 --raw --eol CR
```

- COM 번호는 연결 환경에 따라 변할 수 있다.
- 시리얼 구성은 `115200, 8N1`.
- miniterm 종료는 `Ctrl+]`.
- **miniterm을 먼저 연 다음 Raspberry Pi 전원을 연결**하면 초기 로그 수집에 유리하다.

**첫 이미지에서 확인한 출력:**

```text
--- Miniterm on COM9  115200,8,N,1 ---
Poky (Yocto Project Reference Distro) 6.0.4 raspberrypi4-64 /dev/ttyS0
raspberrypi4-64 login:
```

첫 부팅 자체는 성공했지만 `triton`, `raspberry`, `pi`, `root` 로그인은 실패했다. 기존 Raspberry Pi OS의 계정이 **새 Yocto 이미지에 자동으로 존재하는 것은 아니다.** 기본 root 로그인 정책을 확인하고 개발용 Fragment로 재빌드했다.

---

## 6. root 로그인 허용 및 이미지 재빌드

### 6.1 Yocto 6.0 개발용 Configuration Fragment

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build` / Yocto 환경 활성화**

```bash
cd ~/study/rootfs/yocto
source bitbake-builds/poky-wrynose/build/init-build-env

bitbake-config-build show-fragment \
  core/yocto/root-login-with-empty-password
```

**실제 출력 중 핵심:**

```bitbake
BB_CONF_FRAGMENT_SUMMARY = "Log in as root without password on serial console and over ssh (use with caution)."
EXTRA_IMAGE_FEATURES += "allow-empty-password empty-root-password allow-root-login"
```

**활성화 명령** (동일 WSL 빌드 환경):

```bash
bitbake-config-build enable-fragment \
  core/yocto/root-login-with-empty-password
```

**실제 출력:**

```text
Fragment core/yocto/root-login-with-empty-password added to
/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/conf/toolcfg.conf.
```

여기서는 **새 계정을 만든 것이 아니라**, 개발용 이미지에서 root의 빈 비밀번호 로그인을 허용하도록 이미지 기능을 변경했다.

> [!CAUTION]
> 이 Fragment는 의도적으로 인증을 완화한다. **개발·테스트 전용**으로 사용하고, 제품/공개 네트워크용 이미지에서 반드시 제거하고 계정·SSH 보안 정책을 다시 구성해야 한다. 나중에 Target에서 `passwd root`를 실행해도 **Yocto 빌드 설정의 Fragment가 자동으로 비활성화되지는 않는다.**

### 6.2 증분 재빌드

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
bitbake core-image-minimal
```

**실제 출력(요약):**

```text
Parsing of 992 .bb files complete (0 cached, 992 parsed).
2013 targets, 73 skipped, 0 masked, 0 errors.
BB_VERSION       = "2.18.0"
TARGET_SYS       = "aarch64-poky-linux"
MACHINE          = "raspberrypi4-64"
DISTRO_VERSION   = "6.0.4"
Sstate summary: Wanted 5 ... Current 2152 (0% match, 99% complete)
NOTE: Tasks Summary: Attempted 4025 tasks of which 4011 didn't need to be rerun and all succeeded.
```

`4025 - 4011 = 14`개 Task가 BitBake 요약에서 **재실행 불필요로 분류되지 않은 작업**이며, 전체 Task가 성공했다. 이 수치는 14개 Task 모두가 실제로 컴파일됐다는 뜻은 아니다. 최초 이미지 빌드 전체를 반복하지 않고 기존 빌드 결과를 활용했다.

### 6.3 새 이미지 확인·압축 해제·이름 변경

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
DEPLOY=tmp/deploy/images/raspberrypi4-64
IMG="$DEPLOY/core-image-minimal-raspberrypi4-64.rootfs.wic.bz2"

ls -lh "$IMG"
readlink -f "$IMG"
bzip2 -t "$IMG"

bzip2 -dc "$IMG" \
  > ~/study/rootfs/yocto/image-inspection/core-image-minimal-root-login.img

cd ~/study/rootfs/yocto/image-inspection
mv core-image-minimal-root-login.img rpi4-root-login.img
ls -lh rpi4-root-login.img
```

**실제 `readlink -f` 출력:**

```text
/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/deploy/images/raspberrypi4-64/core-image-minimal-raspberrypi4-64.rootfs-20261025083110.wic.bz2
```

이 파일이 root 로그인 설정을 적용한 **두 번째 빌드 이미지**다. 압축 검사·해제·이름 변경 명령은 오류 없이 완료됐다. 이미지 크기는 180,773,888바이트(172.4MiB)로 Windows 측에서 확인했다.

새 `.img`를 Imager에서 다시 기록했고, 기록 과정에서 덮어써지는 **SD 부팅 파티션의 `enable_uart=1`, `console=serial0,115200`을 재설정**했다.

### 6.4 재부팅 후 root 로그인

**실행 위치: Windows PowerShell / miniterm**

```powershell
Python -m serial.tools.miniterm COM9 115200 --raw --eol CR
```

**실제 Target 출력:**

```text
Poky (Yocto Project Reference Distro) 6.0.4 raspberrypi4-64 /dev/ttyS0
raspberrypi4-64 login: root

WARNING: Poky is a reference Yocto Project distribution that should be used for
 testing and development purposes only.

root@raspberrypi4-64:~#
```

경고는 Poky가 제품용 배포판이 아닌 **개발·검증용 참조 배포판**이라는 안내이며, 로그인 실패 메시지가 아니다.

---

## 7. 실장비 시스템·RootFS 검증

다음 명령들은 모두 **Target (UART) / root 셸**에서 실행했다. miniterm에서 여러 줄을 한 번에 붙여넣으면 커널 메시지와 명령이 섞일 수 있으므로 **한 줄씩 입력하는 것을 권장**한다.

### 7.1 사용자 / 커널 / 아키텍처

**실행 위치: Target / 현재 경로: `~` (경로 무관)**

```bash
whoami
uname -a
uname -r
uname -m
cat /etc/issue
```

**실제 출력:**

```text
root
Linux raspberrypi4-64 6.18.33-v8 #1 SMP PREEMPT Thu May 28 02:31:14 UTC 2026 aarch64 GNU/Linux
6.18.33-v8
aarch64
Poky (Yocto Project Reference Distro) 6.0.4 \n \l
```

- `root`: 관리자 셸에서 실행 중이다.
- `6.18.33-v8`: 실장비의 실행 중인 Linux 커널 버전이다. 이후 모듈 `vermagic`과 비교했다.
- `aarch64`: ARM 64-bit 사용자 공간/커널 아키텍처 검증 자료다.
- `/etc/issue`: 로그인 배너의 배포판 정보. `\n`, `\l`은 getty 등에서 해석하는 표시 문자열이다.

**CPU 코어와 CPU 파트 확인** (Target):

```bash
grep -c '^processor' /proc/cpuinfo
cat /proc/cpuinfo | head -n 20
```

**실제 확인:** miniterm 기록에서 명령 입력 일부가 섞였으나 코어 개수 `4`로 읽혔고, `/proc/cpuinfo`에 `CPU part : 0xd08`이 출력됐다. 같은 명령으로 깨끗하게 재확인할 수 있다. `0xd08`은 ARM Cortex-A72를 나타낸다.

### 7.2 RootFS 마운트

**실행 위치: Target / 현재 경로: `~` (경로 무관)**

```bash
cat /proc/cmdline
cat /proc/mounts | grep ' / '
cat /proc/partitions
df -h /
```

**실제 출력(핵심 발췌):**

```text
# /proc/cmdline 끝부분
... root=/dev/mmcblk0p2 rootfstype=ext4 rootwait net.ifnames=0 console=ttyS0,115200

# /proc/mounts
/dev/root / ext4 rw,relatime 0 0

# /proc/partitions
major minor  #blocks  name
 179     0 124999680 mmcblk0
 179     1    133120 mmcblk0p1
 179     2     37273 mmcblk0p2

# df -h /
Filesystem                Size      Used Available Use% Mounted on
/dev/root                30.5M     13.7M     14.3M  49% /
```

**해석:**

- `mmcblk0p1`: 약 130MiB의 부팅 파티션.
- `mmcblk0p2`: 약 36.4MiB의 RootFS 파티션.
- `/dev/root / ext4 rw`: 현재 RootFS가 `/`에 ext4로 읽기·쓰기 마운트되어 있다.
- `df`의 30.5M는 **파티션 크기와 구분되는 파일시스템 사용 가능 공간 기준의 출력**이다.
- 커널 인자 `console=serial0`은 실제 부팅 뒤 `/proc/cmdline`에서 `console=ttyS0,115200`으로 나타났다.

### 7.3 최소 이미지에 없는 프로그램과 파일

**실행 위치: Target / 현재 경로: `~`**

```bash
cat /etc/os-release
ls -l /etc/os-release /usr/lib/os-release
command -v findmnt
command -v sudo || echo 'sudo not installed'
for cmd in gcc g++ ssh dropbear sshd gdb; do
  command -v "$cmd" || echo "$cmd: not installed"
done
```

**실제 출력 발췌:**

```text
cat: can't open '/etc/os-release': No such file or directory
ls: /etc/os-release: No such file or directory
ls: /usr/lib/os-release: No such file or directory
-sh: findmnt: not found
sudo not installed
gcc: not installed
g++: not installed
ssh: not installed
dropbear: not installed
sshd: not installed
gdb: not installed
```

**해석:**

- `core-image-minimal`은 개발 도구를 모두 갖춘 범용 배포판이 아니다.
- `sudo`가 없어도 현재는 `root` 셸이므로 관리자 명령을 직접 실행할 수 있다. 제품 환경에서 상시 root 사용을 권장한다는 뜻은 아니다.
- `/etc/os-release`가 없는 원인은 아직 확인하지 못했다. 원인 분석에는 Image Manifest·Recipe·RootFS 파일 구성 대조가 필요하다.
- `findmnt` 대신 `/proc/mounts`로 RootFS 마운트 상태를 확인했다.
- 타깃에 `gcc`가 없어도 **Host에서 ARM64로 크로스 컴파일**할 수 있다.

---

## 8. Ethernet·DHCP·외부 통신 검증

### 8.1 LAN 연결 전·후의 차이

**실행 위치: Target / 경로 무관**

```bash
ip link show eth0
ip -4 addr show eth0
```

**LAN 연결 전 관찰:**

```text
eth0: <NO-CARRIER,BROADCAST,MULTICAST,UP> ...
```

**LAN 케이블 연결 후 실제 커널 로그:**

```text
bcmgenet fd580000.ethernet eth0: Link is Up - 1Gbps/Full - flow control rx/tx
```

**LAN 연결 후 실제 출력:**

```text
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether 2c:cf:67:8c:2a:f5 ...
    inet 10.10.16.193/24 brd 10.10.16.255 scope global eth0
```

- `bcmgenet`: Raspberry Pi 4B에서 동작한 Ethernet 커널 드라이버 이름.
- `UP`: 소프트웨어적으로 인터페이스가 활성화된 상태.
- `LOWER_UP`: 물리적인 링크가 성립한 상태.
- IP 주소 부여는 하드웨어 드라이버가 아니라 **DHCP 등 네트워크 구성 기능의 역할**이다.

### 8.2 DHCP 동작 확인

**실행 위치: Target / UART 부팅 로그 관찰**  
**로그를 다시 관찰하는 방법:** Windows PowerShell에서 miniterm을 먼저 실행한 뒤, Pi에서 정상 `reboot` 또는 전원 재인가.

```powershell
Python -m serial.tools.miniterm COM9 115200 --raw --eol CR
```

**실제 부팅 로그(발췌):**

```text
INIT: Entering runlevel: 5
Configuring network interfaces...
udhcpc: started, v1.37.0
udhcpc: broadcasting discover
bcmgenet fd580000.ethernet eth0: Link is Up - 1Gbps/Full - flow control rx/tx
udhcpc: broadcasting select for 10.10.16.193, server 10.10.16.253
udhcpc: lease of 10.10.16.193 obtained from 10.10.16.253, lease time 604800
/etc/udhcpc.d/50default: Adding DNS 164.124.101.2
/etc/udhcpc.d/50default: Adding DNS 164.126.63.1
ip: SIOCGIFFLAGS: No such device
Starting syslogd/klogd: done
```

이로써 `udhcpc`가 IP를 **자동 할당받았음**을 확인했다. DNS 서버 주소 추가 로그도 보였지만 **도메인 이름 해석 자체를 별도로 테스트한 것은 아니다.** `ip: SIOCGIFFLAGS: No such device`는 발생 당시에도 `eth0`·DHCP가 동작했으므로, 원인을 추가로 살필 비치명적 경고로 기록한다.

### 8.3 외부 IP 통신

**실행 위치: Target / 경로 무관**

```bash
ping -c 4 1.1.1.1
```

**실제 출력:**

```text
4 packets transmitted, 4 packets received, 0% packet loss
round-trip min/avg/max = 4.161/4.748/5.456 ms
```

**판정:** Ethernet 물리 링크, IPv4 주소 부여, 외부 IP 대상 ICMP 통신까지 검증됐다. 이는 SSH 서버가 설치되어 있다는 의미는 아니다.

---

## 9. root 비밀번호 변경 및 재부팅

### 9.1 비밀번호 변경

**실행 위치: Target / `root@raspberrypi4-64:~#`**

```bash
command -v passwd
passwd root
```

**실제 출력:**

```text
/usr/bin/passwd
Changing password for root
New password:
Retype password:
passwd: password for root changed by root
```

비밀번호 자체는 문서·GitHub·터미널 로그에 기록하지 않는다. `passwd`로 바꾼 결과는 **현재 SD 카드의 실행 중인 RootFS**에 반영된다. 같은 Yocto 설정으로 다시 이미지를 기록하면 이 변경이 자동으로 이식되지는 않는다.

### 9.2 동기화 후 재부팅

**실행 위치: Target / 경로 무관**

```bash
sync
reboot
```

- `sync`: 보류 중인 파일시스템 쓰기를 저장장치에 반영하도록 한다.
- `reboot`: 정상 종료 절차 뒤 재부팅한다. 일반적으로 별도 `sync` 없이도 파일시스템 동기화가 수행된다.

**재부팅 뒤 실제 관찰:** `raspberrypi4-64 login: root` → `Password:` → Poky 경고 → root 셸 진입. 이후 `whoami`가 `root`로 출력됐다. 따라서 **비밀번호 변경 후 재부팅·재로그인 성공**을 확인했다.

### 9.3 시간 설정은 별도 과제

**실행 위치: Target / 경로 무관**

```bash
date -u
```

**실제 출력:**

```text
Fri Mar  9 12:51:02 UTC 2018
```

실습일과 다른 시간이므로 **시계 동기화 문제는 미해결** 상태다. Raspberry Pi 4B의 전원 재인가 시 시간 유지, NTP 클라이언트·설정 여부는 추후 분석한다. 재부팅 로그에서 파일 시간도 2018년처럼 나타날 수 있으므로, 파일 타임스탬프만으로 빌드 시점을 판단하지 않는다.

---

## 10. 외부 커널 모듈 빌드와 동작 검증

기본 UART·Ethernet 드라이버의 동작과 별개로, 작성한 `.ko`를 대상 커널에 맞게 빌드하고 실제 보드에서 로드·제거하는 과정까지 검증했다.

### 10.1 모듈 빌드 가능 조건 확인

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build

find tmp/work-shared/raspberrypi4-64 \
  -name .config -type f \
  -exec grep -H '^CONFIG_MODULES=' {} \;

bitbake -e virtual/kernel |
  grep -E '^(B|STAGING_KERNEL_DIR|STAGING_KERNEL_BUILDDIR|KERNEL_VERSION)='
```

**실제 출력:**

```text
tmp/work-shared/raspberrypi4-64/kernel-build-artifacts/.config:CONFIG_MODULES=y

B="/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/work/raspberrypi4_64-poky-linux/linux-raspberrypi/6.18.33+git/linux-raspberrypi4_64-standard-build"
KERNEL_VERSION="6.18.33-v8"
STAGING_KERNEL_BUILDDIR="/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/work-shared/raspberrypi4-64/kernel-build-artifacts"
STAGING_KERNEL_DIR="/home/kccistc/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/work-shared/raspberrypi4-64/kernel-source"
```

**해석:**

- `CONFIG_MODULES=y`: 커널이 외부 모듈 로딩 기능을 지원하도록 빌드되었다.
- `STAGING_KERNEL_DIR`: 커널 소스.
- `STAGING_KERNEL_BUILDDIR`: 커널 빌드에 필요한 산출물.
- `KERNEL_VERSION=6.18.33-v8`: 실장비에서 확인한 `uname -r`과 일치.

**실행 위치: Target / UART / 경로 무관**

```bash
cat /proc/sys/kernel/modules_disabled
cat /proc/modules
ls -ld /lib/modules/$(uname -r)
command -v insmod
command -v rmmod
command -v dmesg
```

**실제 출력:**

```text
0
# /proc/modules에는 출력 없음
ls: /lib/modules/6.18.33-v8: No such file or directory
/sbin/insmod
/sbin/rmmod
/bin/dmesg
```

당시 로드된 별도 모듈이 없었고 `/lib/modules/<버전>`도 없었다. 그렇더라도 **정확히 빌드한 `.ko`를 `insmod`로 직접 로드하는 것은 가능할 수 있다.** 아래 실습에서 실제 성공했다. 현재 UART와 LAN 드라이버는 이미 동작했으며, `/proc/modules`가 빈 점을 고려하면 커널 **built-in 드라이버로 포함됐을 가능성이 높다.**

### 10.2 Custom Layer 및 소스 구성

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
cd ~/study/rootfs/yocto/bitbake-builds/poky-wrynose/build
LAYER=../layers/meta-yocto-lab

test -d "$LAYER" || bitbake-layers create-layer "$LAYER"
bitbake-layers show-layers | grep -q 'meta-yocto-lab' ||
  bitbake-layers add-layer "$LAYER"

MOD="$LAYER/recipes-kernel/hello-drv"
mkdir -p "$MOD/files"
```

**최종 소스 구성(이 경로에 파일을 만든다):**

```text
poky-wrynose/layers/meta-yocto-lab/
└── recipes-kernel/
    └── hello-drv/
        ├── hello-drv_1.0.bb
        └── files/
            ├── hello_drv.c
            └── Makefile
```

저장소에 분리해 둔 코드는 [hello-drv 예제](../examples/hello-drv/README.md)에서 확인할 수 있다. 아래에는 실습 당시 사용한 소스 내용을 함께 보존한다.

**`files/hello_drv.c` 전체 내용:**

```c
/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/init.h>
#include <linux/module.h>
#include <linux/printk.h>

static int __init hello_drv_init(void)
{
  pr_info("hello_drv: loaded\n");
  return 0;
}

static void __exit hello_drv_exit(void)
{
  pr_info("hello_drv: unloaded\n");
}

module_init(hello_drv_init);
module_exit(hello_drv_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Yocto kernel module test");
```

**`files/Makefile` 전체 내용:**

```makefile
obj-m := hello_drv.o

all:
	$(MAKE) -C $(KERNEL_SRC) O=$(O) M=$(CURDIR) modules

modules_install:
	$(MAKE) -C $(KERNEL_SRC) O=$(O) M=$(CURDIR) modules_install
```

> Makefile에서 `$(MAKE)` 앞은 **공백이 아니라 탭(Tab)** 이어야 한다. `obj-m`은 `hello_drv.o`를 커널 로더용 모듈 `.ko`로 빌드하도록 Kbuild에 알려준다.

**`hello-drv_1.0.bb` 전체 내용:**

```bitbake
SUMMARY = "Hello kernel module for Raspberry Pi 4"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://hello_drv.c;beginline=1;endline=1;md5=a9f1449b768f69dcffc44cb5e556b102"

SRC_URI = "file://hello_drv.c file://Makefile"
S = "${UNPACKDIR}"

inherit module
```

이 실습의 `LIC_FILES_CHKSUM`은 `hello_drv.c`의 첫 줄 SPDX 주석을 기준으로 계산한 값이다. 첫 줄을 변경하면 체크섬도 다시 계산해야 한다. `inherit module`은 Yocto가 현재 타깃 커널을 기준으로 외부 모듈을 빌드하도록 연결하는 핵심이다.

**위 세 파일을 그대로 생성하려면** WSL에서 `MOD`를 지정하고 편집기(`nano "$MOD/files/hello_drv.c"`, `nano "$MOD/files/Makefile"`, `nano "$MOD/hello-drv_1.0.bb"`)로 저장한다. 원본 BSP Layer는 직접 수정하지 않는다.

### 10.3 모듈 빌드 및 호환성 확인

**실행 위치: WSL / 작업 경로: `.../poky-wrynose/build`**

```bash
bitbake hello-drv
find tmp/work -type f -name 'hello_drv.ko'
```

**실제 `find` 출력:**

```text
tmp/work/raspberrypi4_64-poky-linux/hello-drv/1.0/sources/hello_drv.ko
```

`bitbake hello-drv`의 전체 Task 로그는 이 문서에 포함되지 않았지만, 생성된 `.ko` 파일의 형식과 실장비 삽입·제거 결과를 별도로 확인했다.

**모듈 파일 확인** (동일 WSL 빌드 경로):

```bash
KO=tmp/work/raspberrypi4_64-poky-linux/hello-drv/1.0/sources/hello_drv.ko
file "$KO"
strings "$KO" | grep '^vermagic='
```

**실제 출력:**

```text
.../hello_drv.ko: ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), BuildID[sha1]=64169c366ca227bc8a9f6d26011b911b55f26774, not stripped
vermagic=6.18.33-v8 SMP preempt mod_unload modversions aarch64
```

- `ELF 64-bit ... ARM aarch64`: x86-64 Host에서 **ARM64용** 모듈을 만들었다.
- `vermagic=6.18.33-v8 ...`: 실장비의 커널 버전과 모듈의 빌드 호환성 정보가 일치한다.
- `vermagic` 일치만으로 로딩 성공이 보장되지는 않으므로 `insmod`로 실증해야 한다.

> [!TIP]
> 이 `file`/`strings` 명령을 **Raspberry Pi**에서 먼저 실행했을 때 `file: not found`, `No such file or directory`가 나왔다. 그 시점에는 `.ko`가 **WSL에만 존재했기 때문**이다. 경로가 같은 것처럼 보이더라도 Host와 Target의 파일시스템은 서로 다르다.

### 10.4 SSH 없이 HTTP로 `.ko` 전송

현재 Target에는 `ssh`·`sshd`·`dropbear`가 없어 `scp` 접속을 전제로 할 수 없었다. 반면 `wget`은 존재했다.

**실행 위치: Target / 경로 무관**

```bash
command -v wget
```

**실제 출력:**

```text
/usr/bin/wget
```

**Windows에서 Host 파일 경로 확인** (실행 위치: Windows PowerShell):

```powershell
$src = '\\wsl.localhost\Ubuntu-22.04\home\kccistc\study\rootfs\yocto\bitbake-builds\poky-wrynose\build\tmp\work\raspberrypi4_64-poky-linux\hello-drv\1.0\sources'
Test-Path "$src\hello_drv.ko"
ipconfig
```

`Test-Path`가 `True`라면 Windows에서 WSL 파일에 접근 가능한 상태다. 실제 파일 서버 동작과 다운로드 성공은 이후 로그로 확인했다. 당시 Windows의 네트워크 주소는 `10.10.16.3`이었다.

**HTTP 서버 실행** (Windows PowerShell / 위 `$src` 변수가 설정된 **같은 창**):

```powershell
python -m http.server 8000 --bind 0.0.0.0 --directory $src
```

서버 창을 유지한 상태에서 Target이 아래 주소로 접근한다. 방화벽에서 8000/TCP가 차단되어 있다면 허용 여부를 점검해야 한다.

**다운로드** (실행 위치: Target / 작업 경로: `/tmp`):

```bash
cd /tmp
wget http://10.10.16.3:8000/hello_drv.ko
ls -lh /tmp/hello_drv.ko
```

**실제 출력:**

```text
Connecting to 10.10.16.3:8000 (10.10.16.3:8000)
saving to 'hello_drv.ko'
hello_drv.ko  100% |********************************| 6232  0:00:00 ETA
'hello_drv.ko' saved
-rw-r--r-- 1 root root 6.1K ... /tmp/hello_drv.ko
```

처음에는 LAN 미연결 상태에서 `No route to host`가 발생했다. LAN 연결 후 다음 명령으로 네트워크 경로를 확인했다.

**실행 위치: Target / 경로 무관**

```bash
ip link show eth0
ip -4 addr show eth0
ping -c 3 10.10.16.3
```

**실제 출력(요약):**

```text
eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
inet 10.10.16.193/24 ...
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.311/0.476/0.634 ms
```

> **보안:** `python -m http.server`는 개발용 간이 서버이며 인증·암호화를 제공하지 않는다. 신뢰할 수 있는 로컬 네트워크에서 파일 전송에만 사용하고, 완료 후 Windows 서버 창에서 `Ctrl+C`로 종료한다. `0.0.0.0`은 모든 IPv4 인터페이스에서 서버가 대기한다는 뜻이다.

### 10.5 모듈 삽입·로그 확인·제거

**실행 위치: Target / 작업 경로: `/tmp` / root 셸**

```bash
cd /tmp
insmod /tmp/hello_drv.ko
dmesg | tail -n 10
cat /proc/modules | grep hello_drv
rmmod hello_drv
dmesg | tail -n 10
```

**실제 출력(핵심):**

```text
[ 1647.294570] hello_drv: loading out-of-tree module taints kernel.
[ 1647.300781] hello_drv: loaded

hello_drv 12288 0 - Live 0xffffffe55a0fc000 (O)

[ 1671.030510] hello_drv: unloaded
```

**해석:**

- `insmod`: `.ko`를 커널에 적재하고 `module_init()`으로 등록한 함수를 실행한다.
- `hello_drv: loaded`: **직접 작성한 초기화 함수가 실제 실행**되었다.
- `/proc/modules`의 `Live`: 로드된 상태. `(O)`는 외부(out-of-tree) 모듈을 나타낸다.
- `rmmod`: 모듈을 제거하고 `module_exit()`으로 등록한 함수를 실행한다.
- `hello_drv: unloaded`: **종료 함수도 실제 실행**되었다.
- `taints kernel`: 외부 모듈 로드 사실을 기록하는 커널 표시다. 이번 실습의 실패 메시지가 아니다.

**실험 판정:** `hello_drv.ko`의 크로스 컴파일 → Target 전송 → 삽입 → `/proc/modules` 확인 → 제거가 모두 성공했다. **SD 카드 이미지 재기록 없이 수행했다.**

다만 이는 **하드웨어를 직접 다루지 않는 Hello Module**이다. GPIO 제어, 인터럽트, Character Device, Device Tree 바인딩까지 성공했다는 뜻은 아니다.

---

## 11. 문제·원인·해결 기록

| 증상 / 질문 | 실제 확인 / 원인 | 해결 / 후속 조치 |
|---|---|---|
| 7인치 DSI LCD에 로그가 잠깐 나오고 화면이 사라짐 | LCD Overlay 명시 설정이 없었음. **원인 확정은 못함** | UART 콘솔에서 부팅 상태 확인. LCD는 별도 과제로 분리 |
| `root` 로그인이 거부됨 | 최초 이미지의 개발용 root 로그인 허용 정책 미적용 | `root-login-with-empty-password` Fragment 활성화 → 이미지 증분 재빌드·재기록 |
| SD에 설정한 UART 옵션이 재기록 후 사라짐 | 이미지 재기록은 Boot 파티션까지 덮어씀 | `config.txt`, `cmdline.txt`에 UART 설정 재적용 |
| `findmnt`, `gcc`, `sudo`, `sshd` 없음 | `core-image-minimal`의 실제 패키지 구성에 해당 명령이 없음 | `/proc/mounts` 대체, Host 크로스 컴파일, SSH 추가는 별도 과제 |
| `/etc/os-release` 없음 | 파일이 없는 것까지만 확인됨 | Image Manifest와 패키지·파일 출처 대조 필요 |
| `date -u`가 2018년 | 정상 시각 동기화 전으로 보임 | NTP/시각 유지 방법 점검 필요 |
| `ip: SIOCGIFFLAGS: No such device` | 부팅 중 출력. `eth0`·DHCP는 정상 확인 | 잘못된 인터페이스 참조 가능성 조사 필요 |
| `No route to host` (wget) | 당시 Pi와 Host의 IP 통신 실패 | LAN 연결 → `LOWER_UP`, ping 3/3 확인 → 재다운로드 성공 |
| Target에서 `file` 또는 `.ko` 경로를 찾지 못함 | 빌드 산출물은 WSL 파일시스템에 존재 | WSL에서 `file`/`strings` 실행하고 Target에는 파일 전송 |
| `/lib/modules/6.18.33-v8` 없음 | 이미지에 모듈 설치 디렉터리 미포함 | 직접 `insmod /tmp/hello_drv.ko`로 로드 성공. 일반적 모듈 관리 환경은 별도 구성 |

### 추가로 배운 중요한 구분

**1. 드라이버가 동작한다 ≠ 새로운 드라이버를 개발할 준비가 전부 끝났다**

UART(`ttyS0`)와 Ethernet(`bcmgenet`)은 기본 이미지에서 이미 동작했다. 하지만 별도 `.ko`의 빌드 환경, ABI·커널 버전, 파일 전송, 모듈 삽입 여부는 따로 확인해야 한다.

**2. Built-in 드라이버 ≠ Loadable Module**

`/proc/modules`가 비어 있어도 UART·Ethernet이 동작할 수 있다. 드라이버가 커널 이미지에 정적으로 포함되면 `.ko`로 로드된 항목에 나타나지 않는다. 반대로 `hello_drv`는 `/proc/modules`에 실제로 나타났다.

**3. RootFS를 수정한다 ≠ Yocto 레시피가 바뀐다**

Target에서 `passwd root`를 실행하면 현재 SD 카드의 파일이 바뀐다. 하지만 `bitbake core-image-minimal`이 만든 원본 이미지나 Layer·Recipe 설정이 자동으로 수정되는 것은 아니다.

**4. 모든 변경에 SD 카드 재기록이 필요한 것은 아니다**

| 실습 종류 | 보통 필요한 배포 방식 |
|---|---|
| RootFS/빌드 산출물 읽기·분석 | 별도 배포 불필요 |
| Target에서 비밀번호·설정 파일 수정 | 즉시 적용 또는 재시작. SD 재기록 불필요 |
| Hello `.ko` 테스트 | 개별 파일 전송 + `insmod`. SD 재기록 불필요 |
| 이미지에 앱·SSH·패키지를 재현 가능하게 포함 | BitBake로 이미지 재빌드 후 새 이미지/패키지를 타깃에 적용 |
| 커널·DTB를 변경 | 빌드 후 커널·DTB 또는 전체 이미지를 타깃에 재배포해야 함 |

다른 커널·Toolchain 환경과의 모듈 호환성은 커널 버전과 빌드 설정을 별도로 대조해야 한다. 이번 실습은 **현재 Yocto 이미지와 커널에 대한 외부 모듈 빌드·적재 성공**을 확인한 결과다.

---

## 12. 검증 결과와 미해결 항목

### 실습 최종 체크리스트

- [x] `core-image-minimal` 산출물에서 `.wic.bz2`, `Image`, DTB 구분
- [x] 172.4MiB MBR 이미지, Boot FAT32 130MiB + Linux RootFS 약 36.4MiB 확인
- [x] SD 카드와 Windows 시스템 SSD 구분 후 Raspberry Pi Imager 기록
- [x] SD Boot 파티션의 UART 설정 적용
- [x] Poky 6.0.4의 UART 로그인 콘솔(`/dev/ttyS0`) 확인
- [x] 개발용 root 로그인 Fragment 설정 → 이미지 증분 재빌드 → SD 재기록
- [x] 실장비 root 로그인 및 비밀번호 변경·재부팅 후 로그인 확인
- [x] `6.18.33-v8`, AArch64, Cortex-A72 4코어 확인
- [x] RootFS ext4 읽기·쓰기 마운트 및 공간 확인
- [x] Ethernet 1Gbps, DHCP IPv4 주소, 외부 IP `ping` 0% 손실 확인
- [x] `CONFIG_MODULES=y`, Kernel Source/Build 디렉터리 확인
- [x] `hello_drv.ko` ARM64 크로스 컴파일 및 `vermagic` 확인
- [x] HTTP를 통한 모듈 전송, `insmod`, `dmesg`, `rmmod` 실장비 성공
### 추가 분석 대상

- DSI LCD 화면 출력 중단 원인
- `/etc/os-release` 파일 부재와 RootFS 패키지 구성의 관계
- 타깃 시스템 시간 동기화 및 부팅 시 `ip` 경고 원인
- 개발용 root 로그인 완화 설정 제거와 배포 환경 보안 설정

### 참고 자료

- Yocto 6.0 문서: <https://docs.yoctoproject.org/6.0/>
- meta-raspberrypi BSP: <https://git.yoctoproject.org/meta-raspberrypi/>
- Linux Kbuild 외부 모듈: <https://docs.kernel.org/kbuild/modules.html>

---

**최종 요약:** Raspberry Pi 4B에서 Yocto Poky 6.0.4 기반 ARM64 Linux를 SD 카드로 부팅했다. UART root 로그인, 실제 커널·RootFS, Ethernet/DHCP/외부 통신을 검증했다. 나아가 **이미지를 다시 기록하지 않은 상태에서** Yocto Host로 직접 빌드한 `hello_drv.ko`를 LAN으로 전송해 실장비 `insmod`·`rmmod`까지 성공했다.

---

## 관련 기술 자료

- [ARM64 이미지 빌드와 산출물 검증](03-arm64-image-build.md) — 최초 이미지(`20261025055346`)와 root 로그인 설정 변경 후 이미지(`20261025083110`)를 구분
- [hello-drv 커널 모듈 소스 및 Recipe](../examples/hello-drv/README.md) — 실습에 사용한 모듈 코드와 빌드 메타데이터
