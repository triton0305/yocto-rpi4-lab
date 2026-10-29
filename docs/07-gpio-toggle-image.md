# Chapter 7 — 8채널 GPIO 소프트웨어 재사용과 이미지 통합 설계

> **대상:** Raspberry Pi 4B / ARM64 / `core-image-minimal` 기반
>
> **재사용 성과:** 버튼 8개·LED 8개 전체 독립 토글 실장비 동작 확인
>
> **이 장의 역할:** 기존 드라이버·앱을 Yocto의 모듈 패키지·Device Tree·RootFS·부팅 서비스에 연결하는 설계

## 1. 검증한 기능과 원본 구현

`linux-system-programming`에서 구현한 `lab_gpio.ko` Platform Driver와 `lab_gpio_test`를 재사용한다. **2026-10-29 사용자가 실제 장비에서 버튼 8개와 LED 8개 전체의 독립 토글을 확인했다.** 이 결과는 기존 실행 시스템의 GPIO 기능 검증에 해당한다.

기존 단일 채널 실습에서는 Platform 바인딩·장치 노드 생성, LED 물리 ON/OFF, API selftest, 열린 FD의 unbind 후 `ENODEV`, rebind 후 복구도 관찰했다. 드라이버 수명 관리와 API 구현 설명은 원본 저장소의 책임으로 유지한다.

| 원본 구성 | 역할 | 고정 revision의 소스 |
|---|---|---|
| `lab_gpio.ko` | DT 노드별 GPIO 확보·문자 장치 제공 | [driver/lab_gpio.c](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/driver/lab_gpio.c) |
| `lab_gpio_test` | 8채널 토글 컨트롤러·운영 명령 | [userspace/lab_gpio_test.c](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/userspace/lab_gpio_test.c) |
| 공통 UAPI | 모듈과 앱의 상태·제어 계약 | [include/lab_gpio_uapi.h](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/include/lab_gpio_uapi.h) |
| 8채널 Overlay | 노드·GPIO 속성의 소스 템플릿 | [dt/lab-gpio-eight-overlay.dts](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/dt/lab-gpio-eight-overlay.dts) |
| 모듈·앱 Recipe | Yocto 패키징 연결점 | [lab-gpio](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio_1.0.bb) · [lab-gpio-test](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch07-platform-gpio/yocto/lab-gpio-test_1.0.bb) |

소스 조회 기준은 **`56a431d1e633d90f1bfe98a3a7bfaa026494862c`**다. 이는 검토한 원본 revision이며, 당시 보드에 사용한 모든 바이너리·Overlay의 revision을 소급 확정하는 값은 아니다.

## 2. 현재 소스에서 확인한 운영 인터페이스

기존 앱의 명령 형식:

```bash
lab_gpio_test all toggle start
lab_gpio_test all toggle status
lab_gpio_test all toggle stop
```

현재 소스는 `all`을 D0~D7의 장치 노드 8개로 확장한다. GPIO 번호·극성은 앱 대신 Device Tree에서 결정한다. 앱은 시작 시 LED OFF 초기화를 수행하고 채널별 입력 상태를 관리한다. **20 ms polling·3회 연속 샘플 debounce**는 소스에서 확인한 동작 설정이며 실시간 응답 보장 수치는 아니다.

`start`는 자식 컨트롤러를 만들고 초기화 handshake 후 반환한다. 제어 소켓·잠금은 `/run/lab-gpio`에서 관리하고 `stop`은 컨트롤러 종료와 LED OFF 처리를 수행한다. 이 운영 인터페이스를 부팅 서비스에서 재사용하면 드라이버에 토글 알고리즘을 중복 구현할 필요가 없다.

## 3. Yocto 이미지의 구성 경계

**최종 시스템 목표는 UART 콘솔과 8채널 독립 토글이 부팅 시 자동 실행되는 최소 ARM64 이미지다.** 기존 개별 배포·수동 실행 성과를 바탕으로 아래 통합 구조를 설계했다. 이 장의 이미지 구성·자동 시작은 설계 범위이며 신규 이미지의 부팅 결과로 기술하지 않는다.

| 구성 요소 | 이미지 통합 지점 | 재사용·설계 내용 |
|---|---|---|
| BSP·커널 | `meta-raspberrypi`, `MACHINE=raspberrypi4-64` | 기존 ARM64 부팅 구성 및 타깃 커널 유지 |
| UART | 펌웨어 설정·커널 cmdline·getty | `enable_uart=1`, 실제 콘솔 `ttyS0`·115200 8N1 연결 |
| GPIO 모듈 | 사용자 Layer의 모듈 Recipe | 타깃 커널로 빌드한 모듈 패키지를 RootFS에 선택 |
| GPIO 앱 | `lab-gpio-test` Recipe | `${bindir}/lab_gpio_test` 설치 및 런타임 구성 |
| Device Tree | Overlay 빌드·부팅 파일 배치·적용 설정 | 실제 배선의 8개 노드와 모듈의 `compatible` 연결 |
| 부팅 서비스 | SysV init 스크립트·패키지 | 장치 준비 후 `all toggle start`, 종료 시 `all toggle stop` |
| SD 산출물 | Image Recipe → RootFS → Wic | 모듈·앱·서비스와 부팅 파일을 포함하는 이미지 구성 |

UART의 실장비 설정·출력은 [Chapter 5 §5](05-raspberrypi-boot.md#5-uart-콘솔-설정과-첫-부팅), 기본 이미지 구성은 [Chapter 4](04-rootfs-analysis.md), 모듈·앱의 크로스 빌드 방식은 [Chapter 6](06-custom-layer.md)을 참조한다.

## 4. Recipe·Overlay·자동 시작 연결 원칙

### 모듈·앱을 RootFS에 선택

원본 `lab-gpio` Recipe는 `inherit module`, `S="${UNPACKDIR}/driver"`, `COMPATIBLE_MACHINE="^raspberrypi4-64$"`를 선언한다. 앱 Recipe는 Yocto `${CC}`로 컴파일하고 `${D}${bindir}`에 설치하도록 작성되어 있다.

Image Recipe의 설치 목록에는 **Recipe 이름이 아니라 실제 출력 패키지 이름**을 사용한다. 특히 모듈은 분할 패키지 이름을 확인해 선택하고, 커널 자동 적재 설정은 패키지 설치와 구분한다. 원본 모듈 Recipe에는 자동 적재 설정이 없으므로 여기서 이미 적용된 것으로 서술하지 않는다.

### 실제 배선에 대응하는 DT 유지

원격 8채널 DTS에는 `status = "disabled"`인 템플릿 노드가 있다. **사용자가 확인한 8채널 실장비 성공은 그대로 기록하되, 이 템플릿을 당시 적용한 활성 Overlay·확정 핀맵으로 전용하지 않는다.** 이미지에는 실제 사용한 활성 구성과 그 소스 revision을 대응시키는 방식으로 통합한다.

DTBO를 빌드하는 것, 부팅 파티션에 넣는 것, 펌웨어·부팅 체인에서 적용하는 것은 각각 구분한다. 모듈 자동 적재만으로 DT 장치가 만들어지지 않으며, 실제 적용된 DT 노드와 드라이버가 매칭돼야 `/dev/lab_gpio-*`가 생성된다.

### 기존 SysV init에 맞춰 서비스 구성

기존 메타데이터는 `sysvinit`을 선택했고 실장비 로그에서도 runlevel 5 진입을 확인했다. 자동 실행 설계는 이 구성을 기준으로 한다.

1. 부팅 시 GPIO Overlay 적용과 모듈 적재를 연결한다.
2. `/run`과 D0~D7 장치 노드가 준비된 뒤 컨트롤러를 시작한다.
3. `start`의 초기화 결과와 반환값으로 서비스 시작 상태를 판단한다.
4. 종료 단계에서 `all toggle stop`으로 컨트롤러와 LED 출력을 정리한다.

`start`가 자체 daemon을 만드는 현재 앱 구조를 반영하고, 준비되지 않은 장치를 단순 고정 지연으로 가리지 않는 방식으로 구성한다. 전원 인가부터 probe 이전까지의 전기적 LED 상태는 소프트웨어 초기 OFF와 구분한다.

## 5. 이 저장소에서 보여주는 기술 범위

완료한 Yocto 성과는 **BSP·메타데이터 분석 → 최소 이미지 빌드 → Wic·RootFS 검사 → UART 부팅 → 외부 모듈·앱 크로스 빌드와 타깃 실행**으로 연결된다. 검증된 8채널 GPIO 기능은 이 시스템에 재사용할 소프트웨어 자산이다.

GPIO 구현을 새로 복사하는 대신 고정 revision과 Recipe·DT·서비스 경계를 남겨, 보드 기능을 이미지 구성으로 옮길 때 필요한 시스템 통합 근거를 추적할 수 있게 했다.
