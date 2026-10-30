# Chapter 7 — GPIO 8채널 최종 이미지 구현·검증

> **대상:** Raspberry Pi 4B / ARM64 / Yocto 6.0.4 / `yocto-gpio-toggle-image`
>
> **결과:** 2026-10-29 WIC 빌드·Host 검증, 2026-10-30 최종 이미지의 UART·자동 실행·독립 토글·재부팅·stop/OFF 실장비 확인
>
> **읽는 경로:** 이 장은 실제 소스와 통합 구조, [최종 보고서](final-uart-gpio8-image.md)는 산출물과 증거, [HW 기록](logs/07-gpio-image-hardware-20261030.md)은 UART 결과 요약·사용자 관찰의 범위를 다룬다.

## 1. GPIO Driver·Application 구현 및 검증

직접 개발한 `lab_gpio.ko` Platform Driver와 `lab_gpio_test` C 애플리케이션의 구현 소스는 `linux-system-programming`에서 관리한다. **2026-10-29 실장비에서 버튼 8개·LED 8개의 독립 토글 동작을 확인한 기록**을 바탕으로, 이 장에서는 해당 소프트웨어의 Yocto 이미지 통합 구조를 다룬다.

원격 문서의 2026-10-29 기능 검증 기록에 따르면 단일 채널 구현에서는 Platform 바인딩·장치 노드 생성, LED 물리 ON/OFF, API selftest, 열린 FD의 unbind 후 `ENODEV`, rebind 후 복구도 관찰했다. 드라이버 수명 관리 및 API 구현의 상세 내용은 [개발 소스 저장소](https://github.com/triton0305/linux-system-programming/tree/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio)에 기록했다.

| 구현 구성 요소 | 역할 | Git revision 기준 소스 |
|---|---|---|
| `lab_gpio.ko` | DT 노드별 GPIO 확보·문자 장치 제공 | [driver/lab_gpio.c](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/driver/lab_gpio.c) |
| `lab_gpio_test` | 8채널 토글 컨트롤러·운영 명령 | [userspace/lab_gpio_test.c](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/userspace/lab_gpio_test.c) |
| 공통 UAPI | 모듈과 앱의 상태·제어 계약 | [include/lab_gpio_uapi.h](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/include/lab_gpio_uapi.h) |
| 8채널 Overlay | 노드·GPIO 속성의 소스 템플릿 | [dt/lab-gpio-eight-overlay.dts](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/dt/lab-gpio-eight-overlay.dts) |
| 모듈·앱 Recipe | Yocto 패키징 연결점 | [lab-gpio](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio_1.0.bb) · [lab-gpio-test](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio-test_1.0.bb) |

개발 소스의 조회 기준은 **`56a431d1e633d90f1bfe98a3a7bfaa026494862c`**다. 이 SHA는 소스의 참조 버전을 고정하며, 실장비에 적용했던 바이너리·Overlay의 빌드 리비전과는 구별한다.

## 2. 현재 소스에서 확인한 운영 인터페이스

직접 구현한 GPIO 제어 앱의 명령 인터페이스:

```bash
lab_gpio_test all toggle start
lab_gpio_test all toggle status
lab_gpio_test all toggle stop
```

현재 소스는 `all`을 D0~D7의 장치 노드 8개로 확장한다. GPIO 번호·극성은 앱 대신 Device Tree에서 결정한다. 앱은 시작 시 LED OFF 초기화를 수행하고 채널별 입력 상태를 관리한다. **20 ms polling·3회 연속 샘플 debounce**는 소스에서 확인한 동작 설정이며 실시간 응답 보장 수치는 아니다.

`start`는 자식 컨트롤러를 만들고 초기화 handshake 후 반환한다. 제어 소켓·잠금은 `/run/lab-gpio`에서 관리하고 `stop`은 컨트롤러 종료와 LED OFF 처리를 수행한다. 이 운영 인터페이스를 부팅 서비스에 연결해 토글 알고리즘을 커널 드라이버에 중복 구현하지 않고 사용자 공간에서 유지할 수 있다.

### GPIO 제어 데이터 경로

```text
Raspberry Pi Firmware
  └─ FAT config.txt → lab-gpio-eight-overlay.dtbo
       └─ Device Tree: 8 × compatible = "yocto-lab,gpio-demo"
            └─ lab_gpio.ko: platform probe → gpiod descriptor 획득
                 └─ miscdevice 8개: /dev/lab_gpio-lab-gpio[-d1…-d7]
                      └─ lab_gpio_test: ioctl(GET/SET/OFF)
                           └─ 사용자 공간 컨트롤러: 버튼별 debounce·edge·LED toggle
                                └─ SysV /etc/init.d/lab-gpio: start/status/stop
```

이 흐름에서 **Device Tree는 실제 핀과 극성**, **Platform Driver는 안전한 GPIO 접근 및 UAPI**, **C 애플리케이션은 토글 상태 머신**, **init은 부팅 시 수명 관리**를 담당한다. 사용자 공간의 GPIO 번호를 변경하지 않고도 DTS로 물리 구성을 분리할 수 있다는 점이 설계의 핵심이다.

드라이버의 `lab_probe()`는 먼저 버튼을 `GPIOD_IN`으로 확보한 뒤 LED를 `GPIOD_OUT_LOW`로 확보하고, `misc_register()`로 문자 장치를 노출한다. LED GPIO 획득 이후 cleanup 경로에는 `lab_safe_off()`가 등록되어 있다. `lab_remove()`에 이르는 해제 경로와 열린 FD의 수명을 분리하기 위해 `mutex`·`kref`·`dead` 상태를 사용한다. `read/write/ioctl`은 `dead` 검사를 통과한 경우에만 GPIO를 조작하며, 제거 이후 남은 FD는 `-ENODEV`로 응답한다. [Driver 실제 코드](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/driver/lab_gpio.c).

공통 [UAPI](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/include/lab_gpio_uapi.h)의 계약은 다음과 같다.

| API | 역할 | 검증 및 예외 처리 |
|---|---|---|
| `LAB_GPIO_IOC_OFF` | 지정 채널의 논리 LED OFF 요청 | 제거 상태는 `ENODEV` |
| `LAB_GPIO_IOC_GET` | 버튼 논리 입력과 마지막 성공한 LED 출력 요청값 조회 | ABI version·예약 필드가 포함된 16-byte 구조체 |
| `LAB_GPIO_IOC_SET` | `0/1` 논리 LED 제어 | ABI version·입력 범위·예약 필드 검증, 잘못된 요청은 `EINVAL` |

`GET`의 LED 필드는 **마지막으로 성공한 출력 요청값**이며 LED 광학 상태를 읽는 센서는 아니다. `GPIO_ACTIVE_LOW`인 버튼은 커널의 GPIO descriptor API에서 논리값으로 변환하므로 앱에는 `pressed=1`로 전달된다.

### 8채널 컨트롤러의 중복 실행 및 입력 처리

[원본 C 앱](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/files/lab_gpio_test.c)은 `all`을 8개의 장치 경로로 확장한 후 canonical path 정렬로 잠금 획득 순서를 고정한다. `/run/lab-gpio`의 장치별 `flock`과 Unix domain `SOCK_SEQPACKET` 제어 소켓을 사용하여 동작 중인 컨트롤러의 소유권을 확인하고 `status/stop` 요청을 전달한다. `start`는 자식 프로세스와 초기화 handshake를 완료한 후 반환한다.

각 채널은 **20ms 주기 polling, 3회 연속 동일 입력 debounce, 버튼 해제 후 재무장** 로직을 사용한다. 이는 구현된 샘플링 설정이며 관찰된 최악 응답 시간·하드 실시간 보증으로 해석하지 않는다. `stop`은 소켓을 통한 종료를 확인한 후 각 장치에 OFF 요청을 보내는 경로를 갖는다.

## 3. BSP를 보존한 Custom Layer 통합

BSP의 보드·커널 선택과 프로젝트의 소프트웨어 패키징을 분리하기 위해 `meta-raspberrypi` 원본을 수정하지 않았다.
실제 활성 Layer는 기존 센터 WSL의 `meta-yocto-lab` 한 벌이다. 저장소의 Layer 사본은 최종 GPIO 통합 파일만 담는다.
두 Layer를 동시에 BBLAYERS에 등록하지 않으며, 기존 thermal/chain/memory/hello 실습 파일은 활성 위치에 보존했다.
[Layer 설정](../layers/meta-yocto-lab/conf/layer.conf)의 `BBFILES`가 `recipes-*/*/*.bb`를 선택하고 wrynose 호환성을 선언한다.

| 통합 지점 | 실제 파일 | 이미지 결과 |
|---|---|---|
| Module | [lab-gpio Recipe](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/lab-gpio_1.0.bb) | 커널 ABI별 모듈 패키지 |
| Application | [lab-gpio-test Recipe](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/lab-gpio-test_1.0.bb) | `/usr/bin/lab_gpio_test` |
| DT Overlay | [overlay Recipe](../layers/meta-yocto-lab/recipes-bsp/lab-gpio-overlay/lab-gpio-overlay_1.0.bb) | `devicetree/lab-gpio-eight-overlay.dtbo` deploy |
| Service | [autostart Recipe](../layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/lab-gpio-autostart_1.0.bb) | `/etc/init.d/lab-gpio`, S99/K01 등록 |
| Image | [yocto-gpio-toggle-image.bb](../layers/meta-yocto-lab/recipes-core/images/yocto-gpio-toggle-image.bb) | `wic.bz2` / `wic.bmap` |

## 4. Driver·App 패키지와 UAPI 일치

[드라이버 Recipe](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/lab-gpio_1.0.bb)의 실제 입력은
`file://driver/lab_gpio.c file://driver/Makefile file://include/lab_gpio_uapi.h`이며,
`S = "${UNPACKDIR}/driver"`, `inherit module`을 사용한다.
[Makefile](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/driver/Makefile)의 `-I$(src)/../include`가
같은 스테이징 트리의 UAPI에 접근한다. 커널 `KERNEL_SRC`와 Yocto의 빌드 산출물을 사용해 WSL 커널과 혼동하지 않는다.

[앱 Recipe](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/lab-gpio-test_1.0.bb)는
`file://lab_gpio_test.c file://lab_gpio_uapi.h`, `S = "${UNPACKDIR}"`를 사용한다.
`do_compile`의 `${CC} ${CPPFLAGS} ${CFLAGS} ... ${LDFLAGS}`로 AArch64 ELF를 만들고,
`do_install`이 `${D}${bindir}/lab_gpio_test`에 0755로 설치한다.
두 Recipe의 UAPI는 같은 고정 SHA에서 나온 byte 동일 사본이며 이번 문서 작업에서는 C/H/Makefile을 바꾸지 않았다.

**실제 출력 패키지:** `kernel-module-lab-gpio-6.18.33-v8`, `lab-gpio-test`, `lab-gpio-autostart`.
이미지는 `lab-gpio` 메타패키지를 설치하고, `module.bbclass`가 이를 실제 ABI별 모듈 패키지에 의존시킨다.
버전 없는 `kernel-module-lab-gpio` 별칭만 설치하려던 최초 rootfs 빌드는 DNF에서 실패했다.
메타패키지를 통해 Recipe와 출력 패키지의 의존성을 연결한 뒤 실제 manifest에서 포함 여부를 확인했다.
현재 커널 버전 문자열을 Image Recipe에 고정해 문제를 회피하지 않았다.

모듈 설치 위치는 `/lib/modules/6.18.33-v8/updates/lab_gpio.ko.xz`이며,
압축 해제한 모듈과 앱 모두 `readelf`에서 AArch64를 확인했다.
모듈 vermagic과 빌드 `kernel.release`는 일치한다. [Host 근거](logs/07-gpio-image-host.md)를 참조한다.

## 5. DTBO 빌드에서 FAT 적용까지

[최종 이미지의 활성 DTS](../layers/meta-yocto-lab/recipes-bsp/lab-gpio-overlay/files/lab-gpio-eight-overlay.dts)는
고정 SHA의 disabled 템플릿과 구별되는 통합 사본이다. 8개 status를 `okay`로 바꾸고 설명을 수정했으며,
핀 번호·극성·노드명·`compatible = "yocto-lab,gpio-demo"`는 유지했다.
이번 문서 통합에서 이 파일을 다시 변경한 것은 아니다.

| 채널 | DT 노드 | LED BCM offset / flag | 버튼 BCM offset / flag |
|---|---|---|---|
| D0 | `lab-gpio` | 5 / 0 | 4 / 1 |
| D1 | `lab-gpio-d1` | 6 / 0 | 17 / 1 |
| D2 | `lab-gpio-d2` | 12 / 0 | 18 / 1 |
| D3 | `lab-gpio-d3` | 13 / 0 | 27 / 1 |
| D4 | `lab-gpio-d4` | 19 / 0 | 22 / 1 |
| D5 | `lab-gpio-d5` | 16 / 0 | 23 / 1 |
| D6 | `lab-gpio-d6` | 26 / 0 | 24 / 1 |
| D7 | `lab-gpio-d7` | 20 / 0 | 25 / 1 |

0/1은 각각 active-high/active-low이며 숫자는 40핀 헤더의 물리 핀 번호가 아니다.
16개 line offset은 중복 없고 UART GPIO14/15와 겹치지 않는다. 회로 bias·전원 인가 시 수준·다른 Live consumer 점유는 이 표만으로 증명하지 않는다.

1. `inherit devicetree`가 kernel include를 이용해 DTS를 처리하고 overlay의 `-@` 심볼을 생성한다.
2. `do_deploy` 산출물은 `${DEPLOY_DIR_IMAGE}/devicetree/`에 놓인다.
3. Image Recipe는 `do_image_wic[depends]`에 `lab-gpio-overlay:do_deploy`를 연결한다. 과거 deploy 파일이 우연히 남아 있어야만 성공하는 구성을 피했다.
4. `IMAGE_BOOT_FILES`에 `devicetree/lab-gpio-eight-overlay.dtbo;overlays/lab-gpio-eight-overlay.dtbo`를 추가한다.
5. BSP의 `bootimg-partition`이 FAT에 복사하며 config의 `[all]`에서 `dtoverlay=lab-gpio-eight-overlay`를 활성화한다.

`.dtbo`를 RootFS에 설치하는 것만으로는 firmware의 부팅 적용이 되지 않는다.
실제 WIC의 FAT에서 해당 파일과 활성 config를 추출했고 deploy 산출물과 해시를 비교했다.
Pi DTB와 오프라인 병합한 8개 노드의 phandle/offset/극성을 확인했다.
이 오프라인 결과와 실제 Live DT 원문 확보 여부는 [HW 기록](logs/07-gpio-image-hardware-20261030.md)에서 구분한다.

## 6. UART와 인증 구성

BSP의 `rpi-config_git.bb`, `rpi-cmdline.bb`, `rpi-bootfiles` 배포 흐름을 그대로 사용한다.
이미지의 `do_prepare_gpio_boot`가 bootfiles를 **이미지 전용** `gpio-toggle-boot/`에 복사한다.
공유 BSP config를 덮지 않고 config 끝의 `[all]`에 `enable_uart=1`과 GPIO overlay를 넣는다.
cmdline의 root/bootargs는 보존하고 serial console 인수를 `console=serial0,115200`으로 정규화한다.
기존 lab-gpio overlay나 include가 있으면 임의 병합하지 않고 빌드를 실패시킨다.
U-Boot가 firmware DT를 대체하는 미검증 경로는 `RPI_USE_U_BOOT=1`일 때 거부한다.

실제 FAT의 `kernel8.img`는 deploy `Image`와 일치했다. `serial0`의 오프라인 alias는
`/soc/serial@7e215040`이고, RootFS inittab은 ttyS0 115200 getty를 실행한다.
**2026-10-30 사용자 UART 로그인**으로 실제 운용 결과를 확인했다.

최종 이미지에서만 `debug-tweaks`, `allow-empty-password`, `empty-root-password`를 제거한다.
`shadow` 패키지는 기본 BusyBox에 꺼져 있던 SHA 암호 지원을 보완하고 `/etc/shadow`를 생성한다.
Image Recipe의 rootfs 후처리는 비공개 `GPIO_PASSWORD_FILE`을 읽어 root hash를 설정하고
값을 BitBake 변수나 task 스크립트에 직접 확장하지 않는다. 기존 기본 이미지의 개발용 Fragment는 유지한다.
사용자는 실장비 암호를 변경한 뒤 재부팅 로그인까지 확인했다. 값은 공개하지 않는다.
[로컬 인증 생성과 재현 조건](source-publication-review.md#인증-생성-절차)을 확인한다.

## 7. SysV 자동 시작의 실제 동작

[autostart Recipe](../layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/lab-gpio-autostart_1.0.bb)는
`inherit update-rc.d`, `start 99 2 3 4 5 . stop 01 0 1 6 .`을 선언한다.
필수 런타임은 `lab-gpio-test kmod busybox`다. [init 원문](../layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/files/lab-gpio-init)의 순서는 다음과 같다.

1. tmpfs `/run` 아래 제어 디렉터리를 0700으로 만들고 init 호출 잠금을 확보한다.
2. `modprobe lab_gpio` 실패 시 명확한 실패를 반환한다. 별도 KERNEL_MODULE_AUTOLOAD는 추가하지 않았다.
3. 8개 character node가 준비될 때까지 100ms × 최대 50회 대기한다. 의도적 sleep 합계가 최대 5초이며 프로세스 실행 비용까지 보장하는 실시간 timeout은 아니다.
4. 모두 running이면 재호출하지 않는다. 모두 stopped일 때만 `lab_gpio_test all toggle start`를 한 번 호출한다. 부분 상태는 실패로 처리한다.
5. 각 장치 경로가 정확히 한 번 나오고 8개 모두 `Toggle controller running.`인지 검사한다. 앱 status가 stopped에도 0을 반환할 수 있어 종료 코드만으로 판단하지 않는다.
6. 시작 후 상태 확인 실패 시 원본 stop으로 정리를 시도하고 실패를 반환한다. getty/login은 독립적으로 유지한다.

원본 앱이 자체 fork/ready handshake를 구현하므로 init에서 `&`를 붙이거나 polling daemon을 추가하지 않는다.
20ms polling·3연속 샘플 debounce를 유지해 직접 개발한 동작을 이미지 통합과 분리했다. 버튼 해제 후 재무장하며 짧은 펄스 인식이나 최대 응답 지연을 보장하지 않는다.

`stop`은 원본 stop/OFF 후 모두 stopped를 확인하고, `restart`는 성공한 stop 뒤 start한다.
init `status`는 모두 running이면 0, 아니면 3이다. init 잠금과 앱의 장치별 잠금이 중복 실행을 방지한다.
Host 모의시험 6개는 wrapper의 상태 검사·실패 경로 검증이며 실제 GPIO 시험의 대체물이 아니다.

## 8. 빌드·검증으로 이어지는 추적 경로

| 단계 | 실제 근거 | 범위 |
|---|---|---|
| 소스와 Layer | [고정 리비전](../configs/source-revisions.md), [공개 파일 목록](source-publication-review.md) | Driver/App/UAPI 고정 SHA, 활성 DTS 차이, 활성 Layer와 13개 파일 동일 |
| 개별 Recipe·이미지 | [Task summary 발췌](logs/07-gpio-image-host.md) | 1,512 / 4,128 Tasks 성공. 이번 세션 재빌드 아님 |
| 실제 WIC 내부 | [최종 보고서](final-uart-gpio8-image.md) | FAT/RootFS/ABI/manifest/getty/인증/서비스 |
| Raspberry Pi 동작 | [HW-01~08](logs/07-gpio-image-hardware-20261030.md) | UART 요약·사용자 관찰·미확보 근거 구분 |

기본 이미지의 4,025 Tasks·172.4 MiB WIC와 개별 `hello_drv.ko` 수동 전송은 [Chapter 3](03-arm64-image-build.md)~[Chapter 6](06-custom-layer.md)의 별도 성과다.
최종 시스템은 GPIO Driver·Application·Overlay·SysV 서비스를 한 WIC에 포함하며 사용자의 수동 파일 복사나 start 없이 자동 실행되는 것을 확인했다.

## 9. 실장비 운용 Demo — UART CLI

최종 이미지에서는 SysV 서비스가 시작되므로 별도 수동 `start` 없이 동작한다. 아래는 **타깃에서 운영 상태를 확인하거나 정상 종료·재시작할 때 사용하는 명령**이다. 코드 블록은 실행 방법이며, 출력 결과는 [2026-10-30 HW-01~08 수락 기록](logs/07-gpio-image-hardware-20261030.md)의 사용자 제공 관찰로 구분한다.

```sh
# 부팅 후 자동 실행 상태
/etc/init.d/lab-gpio status
lab_gpio_test all toggle status

# 운영 중 중지: 8채널 컨트롤러 종료 및 LED OFF
/etc/init.d/lab-gpio stop
lab_gpio_test all toggle status

# 정상 복구
/etc/init.d/lab-gpio start
lab_gpio_test all toggle status
```

상태 출력은 장치 경로별로 다음 문자열을 갖는다.

```text
/dev/lab_gpio-lab-gpio: Toggle controller running.
/dev/lab_gpio-lab-gpio-d1: Toggle controller running.
...
/dev/lab_gpio-lab-gpio-d7: Toggle controller running.
```

위 블록의 `...`는 D2~D6 출력의 생략 표기다. 실제 터미널 원문 전체를 재구성한 로그가 아니다. `stop` 이후 각 채널에는 `Toggle controller stopped.`를 기대한다. 영상 시연과 달리 이 CLI 경로는 **실행 상태·제어 명령의 구조를 보여주며**, 버튼 물리 동작은 실장비 관찰과 별도로 판단한다.

## 10. 검증 항목과 재현 근거

| 계층 | 확인된 성과 | 확인 자료 |
|---|---|---|
| Source | 원본 Driver·App·UAPI 고정 revision, 활성 Overlay의 8개 노드 | [소스 관리 기록](../configs/source-revisions.md) · [DTS](../layers/meta-yocto-lab/recipes-bsp/lab-gpio-overlay/files/lab-gpio-eight-overlay.dts) |
| Recipe / Image | 모듈·앱·서비스·DTBO를 한 WIC에 통합, 최종 4,128 Tasks 성공 | [Host 빌드 로그](logs/07-gpio-image-host.md) · [이미지 Recipe](../layers/meta-yocto-lab/recipes-core/images/yocto-gpio-toggle-image.bb) |
| Image 내부 검증 | FAT config/DTBO, ext4 RootFS, 패키지 manifest, AArch64 ELF와 kernel vermagic | [최종 이미지 보고서](final-uart-gpio8-image.md) |
| HW 수락 | UART 로그인, 자동 시작, 8채널 독립 토글 관찰, 재부팅 재확인, stop/OFF | [HW-01~08](logs/07-gpio-image-hardware-20261030.md) |

[HW 수락 기록](logs/07-gpio-image-hardware-20261030.md)은 **사용자 UART 결과 요약**과 **버튼·LED 육안 관찰**을 구분한다. 2026-10-29의 Host 이미지 검사 수치와 2026-10-30의 실장비 수락 결과도 서로 다른 사건이다. 증거 유형을 분리해도 하나의 통합 이미지가 생성되고 실제 장비에서 동작했다는 핵심 결과는 동일하다.

