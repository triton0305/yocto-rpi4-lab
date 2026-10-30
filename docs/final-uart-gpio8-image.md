# UART + GPIO 8채널 최종 이미지

Host 빌드·검사일: 2026-10-29 (Asia/Seoul). 문서 통합·증거 재확인: 2026-10-30.
**SOURCE INSPECTED / RECIPE BUILT / IMAGE BUILT / HOST VERIFIED / HW VERIFIED (사용자 제공 결과 기준).**

2026-10-30 사용자는 최종 WIC의 UART 로그인, 8채널 자동 실행·독립 버튼 토글,
재부팅 후 자동 실행, 정상 stop 및 LED OFF를 확인했다.
[HW-01~08 증거표](logs/07-gpio-image-hardware-20261030.md)는 UART 결과 요약과 육안 관찰을 구분한다.
HW 판정은 사용자 제공 UART 결과 요약·관찰에 근거한다. UART 원문 전체·사진·전기 측정 파일은 별도로 확보되지 않았다.
[Host 증거 발췌](logs/07-gpio-image-host.md)와 [실제 통합 구조](07-gpio-toggle-image.md)를 함께 참조한다.

## 기준선과 변경 정책

WSL2 Ubuntu 22.04.5 x86-64, Yocto 6.0.4 wrynose, poky, raspberrypi4-64,
BitBake 2.18.0, SysVinit을 재사용했다. 결과 저장소 시작 HEAD는
`19a6e8f3b18434a6af17723ded8d1dff7bcf389c`다.
기존 build는 `$HOME/study/rootfs/yocto/bitbake-builds/poky-wrynose/build`.

GPIO 원본은 `56a431d1e633d90f1bfe98a3a7bfaa026494862c`의 `ch07-platform-gpio`.
로컬 원본 HEAD도 같고 해당 디렉터리 tracked diff는 없었다. Driver·App·UAPI·Makefile의 빌드 입력은 위 SHA와 byte 동일성을 확인했다.
2026-10-29 Host 작업 당시 별도의 실장비 검증 SHA/배선 로그는 없었다. 2026-10-30 최종 이미지 동작은 사용자 검증 요약으로 확인했으며, 핀별 배선 사진·전기 측정·Live DT 원문은 추가 확보하지 않았다.

활성 Layer는 기존 `build/../layers/meta-yocto-lab` 한 벌을 유지했다.
결과 저장소의 `layers/meta-yocto-lab`은 **통합 파일만 담은 동기화 사본**이다.
기존 Layer의 thermal/hello/chain/memory/example 등은 활성 위치에 그대로 보존했고,
백업과 전 파일 byte 비교했다. 기존 conf 3개와 BSP checkout도 변경하지 않았다.
이 사본으로 기존 Layer 전체를 교체하거나 BBLAYERS에 중복 등록하지 않는다.

백업: 결과 저장소의 `.local-artifacts/final-gpio/backups/{conf,meta-yocto-lab}`.
2026-10-29 작업의 계획/초기 상태/리비전은 같은 로컬 디렉터리의 `change-plan.txt`,
`initial-git-status.txt`, `revisions.json`. 보관 디렉터리는 gitignore 대상이다.

## 통합 내용

| 파일/기능 | 구현 |
|---|---|
| `recipes-kernel/lab-gpio` | 원본 module Recipe 및 driver/Makefile/UAPI의 고정 SHA 복사본 |
| `recipes-apps/lab-gpio-test` | 원본 Recipe/C 앱/UAPI 복사본; C 및 알고리즘 변경 없음 |
| `recipes-bsp/lab-gpio-overlay` | `inherit devicetree`, 원본 핀/극성 그대로 8개 `okay` 사본 |
| `recipes-core/lab-gpio-autostart` | `inherit update-rc.d`, S99/K01, 원본 자체 daemon 호출 |
| `recipes-core/images/yocto-gpio-toggle-image.bb` | core-image-minimal 기반, 인증·부팅 파티션을 이 이미지에만 적용 |

`module.bbclass`의 빈 `lab-gpio` 메타패키지가 실제 ABI별 모듈 패키지를 의존한다.
확인된 의존은 `kernel-module-lab-gpio-6.18.33-v8`이다. 커널 버전은 Recipe에 고정하지 않았다.
추가 패키지는 앱/모듈/init 및 필수 `kmod`, `shadow`와 그 의존성이다.
`shadow`는 SHA-512 지원 로그인/암호 변경과 shadow 파일 생성을 위해 추가했다.
기본 BusyBox는 `CONFIG_USE_BB_CRYPT_SHA`가 꺼져 있었다. SSH/웹/thermal/hello 패키지는 없다.
BSP/core 기본 네트워크 클라이언트 등은 제거하지 않았다.

### 부팅 경로

실제 BSP `rpi-config_git.bb`가 config와 `RPI_EXTRA_CONFIG`를 처리하고,
`rpi-cmdline.bb`가 cmdline을 생성한다. `rpi-bootfiles:do_deploy`가 양쪽 deploy를 의존한다.
이 구현은 BSP Recipe나 공유 `RPI_EXTRA_CONFIG`를 바꾸지 않는다.
이미지의 `do_prepare_gpio_boot`가 배포된 bootfiles를 전용 `gpio-toggle-boot/`에 복사한다.
config 끝의 `[all]`에 `enable_uart=1`, `dtoverlay=lab-gpio-eight-overlay`를 추가하며,
기존 root 인수를 보존해 cmdline에 `console=serial0,115200`을 단 한 번 넣는다.
기존 lab-gpio 활성 행 또는 config include가 있으면 검토 없이 진행하지 않고 빌드 실패한다.

BSP의 `sdimage-raspberrypi.wks`는 `bootimg-partition`으로 IMAGE_BOOT_FILES를 소비한다.
기존 `bootfiles/*` 선택만 전용 사본으로 대체하며 기존 Kernel/DTB/BSP overlay 목록은 보존한다.
`devicetree/lab-gpio-eight-overlay.dtbo;overlays/lab-gpio-eight-overlay.dtbo`를 추가한다.
Task graph에서 WIC → prepare → rpi-bootfiles deploy와 WIC → overlay deploy를 확인했다.
`RPI_USE_U_BOOT=1`이면 실패하도록 제한했고 실제 FAT의 `kernel8.img`는 deploy `Image`와 동일하다.
오프라인 DT `serial0`은 `/soc/serial@7e215040` (mini-UART), getty는 ttyS0다.
Firmware가 실제 적용하는 pinmux/clock 및 Live DT는 HW에서 확인해야 한다.

### 자동 시작/중지 정책

- 장치: `/dev/lab_gpio-lab-gpio`, `/dev/lab_gpio-lab-gpio-d1` ~ `-d7`.
- `/run`은 fstab의 쓰기 가능한 tmpfs. init은 `/run/lab-gpio`를 0700으로 준비한다.
- 명시적 모듈 적재는 init의 `modprobe lab_gpio` 한 가지. KERNEL_MODULE_AUTOLOAD를 추가하지 않는다.
- 8개 character node 준비를 100ms × 최대 50회 기다린다. 의도적 대기 합계 5초이며 명령 실행 비용은 별도다.
- 모두 running이면 start는 재호출하지 않는다. 모두 stopped일 때만 원본 `all toggle start` 한 번 호출한다.
- 각 장치 경로/정확한 상태/중복/8개 개수를 함께 검사한다. exit 0만으로 running 판정하지 않는다.
- 부분 실행·모듈 실패·장치 timeout은 명확한 실패. init 호출 간 mkdir lock과 원본의 device lock을 활용한다.
- stop은 원본 stop/OFF 후 8개 stopped를 확인한다. restart는 성공한 stop 다음 start다.
- `status`는 모두 running일 때 0, 나머지는 3. 실패 시 getty를 중지하지 않는다.
- 비정상 SIGKILL로 init lock이 남으면 진행 중인 init이 없음을 확인한 뒤 빈 `/run/lab-gpio/init.lock`만 제거한다. 재부팅하면 tmpfs가 초기화된다.

원본은 사용자 공간 20ms polling, 동일 상태 3샘플 debounce이며 IRQ가 아니다.
초기 OFF 및 stop/OFF는 원본 로직을 유지한 것으로, 실제 광학/전압 OFF를 검증한 것은 아니다.

## 실제 빌드 및 실패 복구

| 실행 | 결과 |
|---|---|
| 4개 Recipe 동시 빌드 | 1,512 Tasks / 1,412 재사용 / 모두 성공 |
| 최초 이미지 | 4,094 Tasks / 4,078 재사용 / rootfs 1 실패: 버전 없는 모듈 별칭이 DNF repo에 없음 |
| 두 번째 이미지 | 4,116 Tasks / 4,103 재사용 / rootfs 1 실패: 기본 최소 이미지에 `/etc/shadow` 없음 |
| 최종 이미지 | 4,128 Tasks / 4,113 재사용 / 모두 성공 |

모듈 별칭 대신 실제 패키지를 의존하는 `lab-gpio` 메타패키지로 Recipe 의존성까지 연결했다.
인증용 `shadow` 추가 후 성공했다. 원본 C 변경, clean/cleansstate/cleanall은 하지 않았다.
성공한 개별/최종 빌드 로그에는 WARNING/ERROR 행이 없었다.

원문 로그: `.local-artifacts/final-gpio/{recipes-build,image-build,image-build-retry,image-build-final}.log`.
Task graph: `task-depends.dot`, 최종 환경: `image-metadata.txt`.

## Host 증거

검사 도구는 `scripts/verify-gpio-wic.py`. 블록 장치에는 접근하지 않고 WIC를 읽어
일반 파일로 압축 해제/파티션 추출한다. native mcopy, debugfs(쓰기 옵션 없음),
readelf/modinfo/fdtget/fdtoverlay로 실제 이미지 내부를 검사한다.

- MBR FAT32(type 0x0c): 시작 sector 8192, 266240 sectors.
- Linux ext4(type 0x83): 시작 sector 278528, 170392 sectors.
- FAT config/cmdline/kernel/overlay를 실제 WIC에서 추출했다. overlay는 deploy와 SHA-256 동일.
- Pi 4 DTB와 overlay를 오프라인 병합해 8개 compatible/status/phandle/GPIO offset/극성을 확인했다.
- LED offsets `5,6,12,13,19,16,26,20`, button offsets `4,17,18,27,22,23,24,25`.
  LED active-high, button active-low. 16개 offset은 중복 없고 UART 14/15와 겹치지 않는다.
  회로 bias/pull 및 다른 Live GPIO consumer 점유까지 입증한 것은 아니다.
- 앱/모듈 AArch64, 설치 모듈은 `/lib/modules/6.18.33-v8/updates/lab_gpio.ko.xz`.
- vermagic: `6.18.33-v8 SMP preempt mod_unload modversions aarch64`.
- manifest에 실제 모듈/app/init/kmod/shadow 포함. 실행 권한 0755, S99/K01 symlink 확인.
- `/sbin/init` → SysVinit, `/bin/login` → shadow, ttyS0 getty 및 securetty 허용 확인.
- root passwd 필드는 `x`, shadow는 UID/GID 0, mode 0400, 비어 있지 않은 `$6$` hash.
  비공개 비밀번호를 다시 해싱해 WIC 내부 root hash와 비교했다. 비밀은 보고서에 저장하지 않았다.
- Host init 모의시험 6개 통과: 정확한 8채널 상태, 중복 시작, stop/restart, 부분 상태,
  modprobe 실패, timeout 50회, 동시 init 잠금. 실제 ARM daemon/GPIO 실행 시험이 아니다.
- bzip2 전체 해제 성공; bmap의 ImageSize 및 모든 mapped range SHA-256 일치.

로컬 증거: `.local-artifacts/final-gpio/verification.log`, `inspection/verification.json`,
`inspection/{app-readelf,module-readelf,module-vermagic,inittab,fstab}.txt`,
`inspection/boot/`, `init-tests.log`, `bmap-verification.txt`, `layer-files.sha256`.
검사 초기에는 shadow mode를 0600으로만 가정해 중단했으나 실제 0400(root 전용 읽기)임을
확인하고 검사를 0400/0600 허용으로 고쳤다. 이미지 보안 권한은 낮추지 않았다.

## 재현

2026-10-29 실제 빌드에 사용한 환경과 명령을 기준으로 재현한다. 기존 Yocto checkout·활성 Layer를 확인한 뒤, [인증 생성 절차](source-publication-review.md#인증-생성-절차)에 따라 새 개발자만의 초기 암호와 hash를 로컬에 준비한다. 인증 파일이 이미 있는 환경에서는 생성 단계를 건너뛰고 보관한 자격 정보를 사용한다. 이 절의 명령은 실행 안내이며 문서 보완 과정에서 새 BitBake 빌드를 수행한 결과는 아니다.

아래는 확인된 기존 디렉터리 배치다. 다른 clone·build 위치에서는 실제 경로를 지정한다.
BSP와 OE-Core 등 checkout은 [리비전 표](../configs/source-revisions.md)의 버전에 맞추고, 기존 `meta-yocto-lab`의 `layer.conf`를 확인한다. 동기화 후 `bitbake-layers show-layers`에서 정확히 한 벌이 활성인지 확인한다. 활성 사용자 Layer가 없는 신규 환경은 [직접 등록 절차](source-publication-review.md#신규-환경의-layer-등록)를 사용하며 아래 동기화 명령은 건너뛴다.

```sh
cd ~/study/rootfs/yocto/yocto-rpi4-lab
python3 scripts/sync-gpio-layer.py \
  ../bitbake-builds/poky-wrynose/layers/meta-yocto-lab \
  .local-artifacts/layer-sync-backups
# 별도 인증 생성 절차를 완료한 상태에서 진행한다. 기존 인증 파일은 재생성하지 않는다.
python3 tests/test_gpio_init.py
source ../bitbake-builds/poky-wrynose/build/init-build-env
bitbake-layers show-layers
bitbake lab-gpio lab-gpio-test lab-gpio-overlay lab-gpio-autostart
bitbake yocto-gpio-toggle-image
```

빌드 후 결과 저장소로 돌아와 다음을 실행한다.

```sh
python3 scripts/verify-gpio-wic.py \
  ../bitbake-builds/poky-wrynose/build/tmp/deploy/images/raspberrypi4-64/yocto-gpio-toggle-image-raspberrypi4-64.rootfs.wic.bz2 \
  ../bitbake-builds/poky-wrynose/build .local-artifacts/final-gpio/inspection
```

원본 복사 갱신은 먼저 새 SHA의 HW 근거를 확인한 뒤 `git show SHA:ch07-platform-gpio/...`로
driver/Makefile/UAPI/app을 같은 SHA에서 가져온다. driver의 `../include` 배열을 보존하고,
앱은 원본 Recipe대로 C/UAPI를 같은 files 디렉터리에 둔다. DTS 변경은 status와 설명뿐이다.
새 SHA/해시/핀 비교를 기록하고 Recipe/WIC 검사를 다시 수행한다. AUTOREV는 사용하지 않는다.

## 인증 및 SD 기록 인계

배포 이미지의 계정은 `root`. 사용자는 실장비에서 비밀번호를 변경하고 재부팅 후 로그인을 확인했다. 변경한 암호는 기록하지 않는다.
아래는 **새로 기록하는 원본 이미지의 초기 암호** 확인 절차이며, 이미 변경한 SD의 현재 암호와 다를 수 있다.
초기 비밀번호는 build의 `conf/gpio-private/root-password.txt`에서 **사용자 로컬 터미널로만** 확인한다.
`root-password.hash`와 함께 파일 mode 0600, 디렉터리 0700이며 공개 저장소 밖에 있다.
비밀을 채팅/README/로그에 붙이지 않는다. 최종 이미지에만 empty-password/debug-tweaks 기능을 제거했다.
다른 core-image-minimal의 개발 Fragment 설정은 보존했다. 자격 파일은 개인적으로 백업한다.
이미지 자체에도 인증 해시가 있으므로 이미지 배포 범위를 관리한다.

Windows PowerShell에서 아래 읽기 전용 명령으로 대상 SD의 번호/모델/SerialNumber/용량을 확인한다.
SD를 분리했을 때 사라지고 다시 연결하면 나타나는 항목을 대조한다.

```powershell
Get-Disk | Select-Object Number,FriendlyName,SerialNumber,BusType,Size,IsBoot,IsSystem
```

기존 정상 카드는 별도 보관하고 새 카드를 권장한다. **기록하면 선택한 카드의 기존 데이터가 지워진다.**
사용자가 대상과 데이터 백업을 확인하고 직접 기록 여부를 선택한다. 이 작업에서 기록은 실행하지 않았다.
사용자는 `inspection/image.wic`을 Windows로 복사하고 `Get-FileHash -Algorithm SHA256`로 아래
비압축 해시와 비교한 뒤 Imager의 사용자 이미지 선택으로 기록할 수 있다.
도구의 OS 사용자/SSH/Wi-Fi 커스터마이징을 적용하지 않는다. 별도 파일 복사는 필요 없다.

다시 배포할 때 실패하면 전원을 끄고 보관한 이전 정상 SD로 교체한다. 기존 SD를 덮어썼다면 사용자가 확보한
전체 이미지 백업으로 직접 복원해야 한다. 이 작업은 기존 SD 백업 생성도 수행하지 않았다.
새 이미지의 config만 바꿔 이전 RootFS를 복구할 수 있다고 가정하지 않는다.

## 사용자 HW-01~08 재검사 절차

먼저 실제 3.3V 회로, LED 저항, 버튼 bias, 논리 극성, BCM offset과 물리 핀 차이를 확인한다.
UART 115200 8N1, flow control 없음으로 부팅 로그와 root 암호 로그인을 확인한다.

```sh
uname -r
cat /proc/cmdline
ls -l /dev/lab_gpio-*
lsmod | grep lab_gpio
dmesg | grep -E 'lab.gpio|ttyS|serial'
ls -l /sys/bus/platform/drivers/lab-gpio/
/etc/init.d/lab-gpio status
lab_gpio_test all toggle status
for n in lab-gpio lab-gpio-d1 lab-gpio-d2 lab-gpio-d3 lab-gpio-d4 lab-gpio-d5 lab-gpio-d6 lab-gpio-d7; do
    printf '%s: ' "$n"
    tr -d '\000' < "/sys/firmware/devicetree/base/$n/status"
    echo
    readlink "/sys/bus/platform/devices/$n/driver"
done
```

1. HW-01: 새 WIC로 UART 부팅/암호 로그인.
2. HW-02: 수동 start 없이 8개 노드/bind 및 모두 running.
3. HW-03: 자동 시작 직후 LED 모두 OFF 실측/관찰.
4. HW-04/05: D0~D7 각각 누름/해제를 충분히 유지해 한 번 ON, 다음 번 OFF; 다른 LED 불변.
5. HW-06: 원본 status의 각 채널 running 확인.
6. HW-07: `reboot` 후 UART/자동 시작/토글 재현.
7. HW-08: `lab_gpio_test all toggle stop` 후 모든 LED OFF와 stopped 확인.
   `/etc/init.d/lab-gpio status`는 이때 3을 반환해야 한다. 필요 시
   `lab_gpio_test all toggle start` 또는 `/etc/init.d/lab-gpio start`로 다시 시작한다.

실패 시 start를 반복하기 전에 UART에서 dmesg, Live DT, 장치/driver bind, status를 수집한다.
오프라인 DT 병합 성공은 실제 firmware 적용 성공의 대체 증거가 아니다.
2026-10-29에는 HW 증거가 없어 미검증으로 남겼다. 2026-10-30 사용자 제공 수락시험 결과를 반영한 최신 판정과 한계는 [HW 증거표](logs/07-gpio-image-hardware-20261030.md)에 있다. 위 명령은 재검사 안내이며 이번에 실행한 UART 원문이 아니다.

## 참고

구현 시 checkout의 `module`, `devicetree`, `update-rc.d`, `rootfs-postcommands` 클래스와
BSP Recipe/WIC 소스를 직접 확인했다. [Yocto 6.0 클래스 문서](https://docs.yoctoproject.org/6.0/ref-manual/classes.html)도 대조했다.

## 이번 산출물

배포 디렉터리: `$HOME/study/rootfs/yocto/bitbake-builds/poky-wrynose/build/tmp/deploy/images/raspberrypi4-64/`.

- 압축 이미지: `yocto-gpio-toggle-image-raspberrypi4-64.rootfs-20261029073227.wic.bz2`
- 크기: **40,615,730 bytes**, bzip2
- SHA-256: `be2a97c59ba7f2c2595130f14de9e09dfcf70ffda0cf3baa9a3d9001e48233eb`
- 비압축 WIC: **229,847,040 bytes**
- 비압축 SHA-256: `ca12e0875eac6a6fff2b4ac19c0be789f46241f210e9a556147e4969ca972ac6`
- Manifest: `yocto-gpio-toggle-image-raspberrypi4-64.rootfs-20261029073227.manifest`
- bmap: `yocto-gpio-toggle-image-raspberrypi4-64.rootfs-20261029073227.wic.bmap`
- 압축 SHA sidecar: `yocto-gpio-toggle-image-raspberrypi4-64.rootfs-20261029073227.wic.bz2.sha256`

절대 경로는 로컬 `inspection/verification.json`에 보관했다. 공개 문서에는 개인 Host 절대 경로를 넣지 않았다.
2026-10-29 Codex Host 작업과 2026-10-30 문서 통합 작업에서는 Git commit/push/tag 및 SD/USB 기록을 실행하지 않았다. 사용자 측 SD 기록·실장비 시험과 구분한다. 원래 작업 트리의 파일 삭제 없음.
