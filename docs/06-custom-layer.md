# Chapter 6 — Custom Layer·외부 모듈·C 앱 Recipe

> **환경:** 센터 WSL x86-64 → Raspberry Pi 4B / Yocto 6.0.4 / Linux `6.18.33-v8` / ARM64
>
> **결과:** 직접 개발한 Linux 모듈·C 테스트 애플리케이션을 Custom Layer에서 ARM64로 크로스 빌드하고, Task 오류 해결·배포 파일 무결성·실장비 실행을 검증

## 1. 목표와 Layer의 책임

`meta-raspberrypi`의 보드 지원 구성과 직접 개발한 소프트웨어를 분리하기 위해 `meta-yocto-lab`에 모듈·앱 Recipe를 구성했다. 최초 `hello-drv`의 Layer 구성과 실장비 적재는 [Chapter 5 §10](05-raspberrypi-boot.md#10-외부-커널-모듈-빌드와-동작-검증)에 기록했다.

직접 구현한 `memory-lab`, `chain-lab`, `thermal-core` 모듈과 C 테스트 애플리케이션을 같은 Yocto 환경에서 빌드했다. 이 문서에서는 크로스 빌드·배포 및 오류 해결을 다루고, 드라이버 알고리즘과 API 테스트 구현은 [linux-system-programming](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/driver/thermal_core.c)에 기록한다.

## 2. 개발 소스와 BitBake 빌드 입력 관리

| 위치 | 역할 | 실제 관리 방식 |
|---|---|---|
| `examples/hello-drv/` | 이 저장소의 검증 예제 | [C·Makefile·Recipe](../examples/hello-drv/README.md) |
| `linux-system-programming/ch06-character/` | 직접 개발한 모듈·앱 소스 | [모듈 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/yocto-recipe/thermal-core_1.0.bb) · [앱 Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/yocto-recipe/thermal-test_1.0.bb) |
| `layers/meta-yocto-lab/recipes-kernel/…/files/` | BitBake가 읽는 모듈 소스 | 개발 원본을 스테이징한 사본 |
| `layers/meta-yocto-lab/recipes-test/…/files/` | 이벤트·스트레스 테스트 앱 소스 | 앱·UAPI 헤더·Recipe를 함께 스테이징 |
| `build/tmp/work/…` | Recipe별 작업·산출물 | BitBake가 관리하는 빌드 영역 |

핵심은 **소스 revision과 Layer에 들어간 입력을 함께 관리하는 것**이다. 개발 원본만 수정하면 Recipe가 오래된 사본을 빌드할 수 있다. 실제 06D 절차는 드라이버·Makefile·공통 헤더를 Layer로 복사하고 `cmp`로 소스 일치를 확인하도록 구성했다. 개발 소스의 참조 Git revision은 [설정 기록](../configs/source-revisions.md#5-외부-모듈gpio-소스-참조-기준)에 고정했다.

## 3. 외부 모듈 Recipe와 Kbuild 연결

실제 [hello-drv Recipe](../examples/hello-drv/hello-drv_1.0.bb)의 핵심:

```bitbake
SRC_URI = "file://hello_drv.c file://Makefile"
S = "${UNPACKDIR}"
inherit module
```

| 요소 | 빌드에서의 의미 |
|---|---|
| `SRC_URI` | Recipe가 가져올 소스와 Makefile 지정 |
| `S` | 압축 해제·스테이징된 모듈 소스 위치 |
| `inherit module` | 타깃 커널의 소스·빌드 산출물과 외부 모듈 빌드 연결 |
| `obj-m` | Kbuild에 로드 가능한 `.ko` 대상 선언 |
| `KERNEL_SRC`, `O`, `M` | 커널 소스, 빌드 출력, 외부 모듈 위치 전달 |
| `modules_install` | 모듈 설치 단계의 Makefile 진입점 |

`hello-drv`에서 확인한 `STAGING_KERNEL_DIR`, `STAGING_KERNEL_BUILDDIR`, `KERNEL_VERSION`은 [Chapter 5 §10.1](05-raspberrypi-boot.md#101-모듈-빌드-가능-조건-확인)에 있다. WSL 자체 커널이 아닌 Pi의 Yocto 커널을 대상으로 빌드했다.

### Makefile `clean` 누락 해결

후속 `chain-lab` 빌드는 `do_configure`의 `make clean`에서 중단됐다. `log.do_configure`에 해당하는 오류를 확인하고 Makefile에 모듈 중간 산출물을 정리하는 `clean:` 규칙을 추가했다. 이후 `do_configure`·`do_compile`과 전체 **1,028 Tasks**가 성공했다.

같은 문제가 `thermal-core`에서도 관찰됐다. 반면 `no_llseek` 선언 오류는 `do_compile`의 커널 API 참조 문제였다. 실패 Task를 구분해 Makefile과 C 소스를 각각 수정했다. 오류 원문과 수정 후 출력은 [검증 로그](logs/06-module-packaging.md)에 보존했다. Chapter 5의 `hello-drv` Makefile은 당시 기록으로 유지한다.

## 4. C 테스트 앱의 타깃 크로스 빌드

직접 작성한 [thermal-test Recipe](https://github.com/triton0305/linux-system-programming/blob/56a431d1e633d90f1bfe98a3a7bfaa026494862c/ch06-character/yocto-recipe/thermal-test_1.0.bb)는 `do_compile`에서 `${CC}`, `${CFLAGS}`, `${CPPFLAGS}`, `${LDFLAGS}`를 사용하고 `do_install`에서 `${D}${bindir}`에 실행 파일을 배치한다.

| 단계 | 역할 | 확인 결과 |
|---|---|---|
| 소스·공통 헤더 스테이징 | 드라이버와 앱이 같은 UAPI를 사용 | 06D 모듈에서 기존 앱 회귀 실행 |
| Recipe의 `do_compile` | Yocto 크로스 컴파일러·sysroot 사용 | `ELF 64-bit … ARM aarch64` |
| Recipe의 `do_install` | 패키징용 임시 루트 `${D}`에 설치 | `thermal-test` Recipe에서 `${bindir}` 경로 선언 |
| 개별 산출물 전송 | 부팅을 검증한 Yocto 이미지에 테스트 파일 전달 | Pi에서 앱 실행·종료 코드 확인 |

06D 이벤트 앱은 **933 Tasks, 914개 재실행 불필요, 전체 성공**을 기록했다. Pi에서는 신규 16개와 기존 앱 회귀 23개·19개를 합쳐 **58/58 PASS**했다. 이는 Recipe로 빌드한 ARM64 바이너리를 실제 타깃에서 실행한 결과다. API·동시성·지연 평가의 상세 내용은 이 저장소에 중복하지 않는다.

### 셸 초기화와 `set -u` 충돌 해결

06C 빌드 스크립트는 `oe-init-build-env`를 읽는 중 `BBSERVER: unbound variable`로 중단됐다. 초기화 구간에서 `set +u`, 초기화 후 `set -u`로 복원해 모듈·앱 빌드를 완료했다. 해당 실행은 **1,047 Tasks 전체 성공**을 기록했다. C 컴파일 오류와 환경 초기화 오류를 분리해 해결한 사례다. [실제 출력](logs/06-module-packaging.md#2-셸-초기화-오류-해결)을 참조한다.

## 5. 배포 파일 검증과 타깃 실행

UART는 명령·로그 콘솔, Ethernet/HTTP는 바이너리 전송 경로로 사용했다. Host에서 ELF 아키텍처와 `vermagic`를 확인한 뒤, 공유 폴더를 거쳐 Pi로 전달했다.

`chain_lab.ko`의 후속 4자원 버전은 **Host 원본·Windows 공유본·Pi 수신본의 SHA-256이 일치**했다. 구버전 파일의 크기·해시와 구분한 뒤 새 모듈의 실행 결과를 확인했다. Pi의 `uname -r` 및 모듈 `vermagic`는 `6.18.33-v8`이었다. 해시와 관련 명령은 [검증 로그](logs/06-module-packaging.md#3-동일한-배포-파일-확인)에 있다.

이 절차로 파일 갱신과 커널에 적재된 모듈의 갱신을 분리했다. 디스크의 `.ko`를 교체해도 이미 적재된 모듈은 바뀌지 않으므로 기존 적재 상태를 조회하고 정상 제거·재적재로 확인했다.

## 6. 이미지 통합으로 연결되는 지점

검증한 배포 방식은 **개별 모듈·앱 빌드 → 파일 전송 → 수동 적재·실행**이다. Layer에 Recipe를 등록하는 일, 패키지를 RootFS에 선택하는 일, 부팅 시 실행하는 일은 각각 별도의 구성이다.

[Chapter 4](04-rootfs-analysis.md)의 RootFS/Wic 분석을 바탕으로, [Chapter 7](07-gpio-toggle-image.md)에서는 직접 개발한 GPIO Driver·Application을 모듈 패키지·Overlay·RootFS·부팅 서비스의 시스템 통합 구성과 연결한다. 실제 빌드 설정과 소스 기준은 [build-config](../configs/build-config.md)·[source-revisions](../configs/source-revisions.md)에서 연결한다.

## 7. 최종 GPIO 이미지와의 차이 및 공개 범위

이 장의 개별 모듈·앱 실행과 HTTP 전송 실증은 그대로 보존한다. 2026-10-29에는 GPIO 모듈·앱·DTBO·SysV 서비스를
`yocto-gpio-toggle-image`에 설치하는 Task 의존성까지 연결했고, 2026-10-30 사용자가 최종 WIC의 자동 실행을 확인했다.
[Chapter 7](07-gpio-toggle-image.md)의 실제 파일 링크에서 `file://` 입력 → Kbuild/교차 컴파일 → 패키지 → Image Recipe의 설치 목록을 추적할 수 있다.

`inherit module`이 생성한 실제 ABI별 출력은 `kernel-module-lab-gpio-6.18.33-v8`이다.
`lab-gpio` 메타패키지가 이를 의존하므로 커널 버전을 Image Recipe에 하드코딩할 필요가 없다.
개별 Recipe 성공, rootfs 패키지 설치, 부팅 시 서비스 시작은 각각 [Host 로그](logs/07-gpio-image-host.md)와
[HW 기록](logs/07-gpio-image-hardware-20261030.md)으로 확인한다.

이 장의 Layer 경로 표는 **센터의 실제 빌드 Layer**를 설명한다. 이 저장소의 Layer에는 최종 GPIO 통합 13개 파일만 포함했고,
`memory-lab`, `chain-lab`, `thermal-core`, thermal 테스트 등을 무작정 복사하지 않았다.
기존 성과·고정 소스 링크·[모듈 검증 로그](logs/06-module-packaging.md)는 유지한다.
