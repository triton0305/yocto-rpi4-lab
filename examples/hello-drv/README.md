# hello-drv — Raspberry Pi 4B 외부 커널 모듈

Yocto Project 6.0.4 (`wrynose`)의 `inherit module`을 이용해 ARM64용 `hello_drv.ko`를 빌드했습니다. Raspberry Pi 4B에서 모듈 전송, `insmod`, `/proc/modules`, `dmesg`, `rmmod`로 동작을 검증했습니다.

검증 명령과 실행 출력은 [Chapter 5 — 외부 커널 모듈 빌드와 동작 검증](../../docs/05-raspberrypi-boot.md#10-외부-커널-모듈-빌드와-동작-검증)에 정리했습니다.

## 파일 구성

- [`files/hello_drv.c`](files/hello_drv.c) — 모듈 초기화·종료 함수와 커널 로그 출력
- [`files/Makefile`](files/Makefile) — Kbuild 기반 커널 모듈 빌드 규칙
- [`hello-drv_1.0.bb`](hello-drv_1.0.bb) — `inherit module`을 사용하는 Yocto Recipe

## 빌드

Yocto Build 환경에서 소스를 사용자 Layer의 `recipes-kernel/hello-drv/` 경로에 배치하고 다음과 같이 빌드합니다.

```bash
bitbake hello-drv
```

생성된 `hello_drv.ko`는 Raspberry Pi 4B에 전송해 `insmod`로 적재하고, `dmesg`와 `rmmod`로 동작 및 제거를 확인했습니다.
