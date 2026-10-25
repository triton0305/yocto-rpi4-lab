# hello-drv — Raspberry Pi 4B 외부 커널 모듈

Yocto Project 6.0.4 (`wrynose`)의 `inherit module`로 빌드한 ARM64 커널 모듈 예제다. Raspberry Pi 4B에서 파일 전송, `insmod`, `/proc/modules`, `dmesg`, `rmmod`를 검증한 기록은 [Chapter 5](../../docs/05-raspberrypi-boot.md#10-외부-커널-모듈-빌드와-동작-검증)에 있다.

## 소스

- [`files/hello_drv.c`](files/hello_drv.c): 로드·언로드 메시지를 출력하는 모듈
- [`files/Makefile`](files/Makefile): Kbuild를 사용하는 외부 모듈 빌드 규칙
- [`hello-drv_1.0.bb`](hello-drv_1.0.bb): Yocto `module` 클래스가 적용된 Recipe

세 파일은 [실장비 기록](../../docs/05-raspberrypi-boot.md#102-custom-layer-및-소스-구성)의 코드와 동일하다. **이 디렉터리는 완전한 Yocto Layer가 아니라, 사용자 Layer의 `recipes-kernel/hello-drv/`에 배치할 Recipe 예제**다.

## 기존 Yocto Build 환경에 배치

`poky-wrynose/build` 환경에서 사용자 Layer의 `recipes-kernel/` 아래에 디렉터리를 복사한다.

```bash
LAYER=../layers/meta-yocto-lab
mkdir -p "$LAYER/recipes-kernel"
cp -r /path/to/yocto-rpi4-lab/examples/hello-drv "$LAYER/recipes-kernel/"
bitbake-layers add-layer "$LAYER" # 아직 등록되지 않은 경우
bitbake hello-drv
```

`/path/to/...`는 실제 Checkout 위치로 변경해야 한다. 이 명령은 재현을 위한 안내이며, 해당 공개 예제를 별도로 다시 빌드했다고 주장하지 않는다.

실장비에서는 `hello_drv.ko`를 수동 전송·적재했으며 이미지 자동 포함·로드나 GPIO 제어는 실습에 포함하지 않았다.
