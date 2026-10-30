# 최종 GPIO 이미지 Host 증거 발췌

2026-10-29 실제 빌드·검사 파일에서 발췌하고 2026-10-30 보존 파일을 다시 대조했다.
새 BitBake 빌드나 보드 실행은 하지 않았다. 개인 절대 경로·인증정보·원시 RootFS는 공개하지 않는다.

## 빌드 요약

로컬 보존 파일 `recipes-build.log`:

```text
NOTE: Tasks Summary: Attempted 1512 tasks of which 1412 didn't need to be rerun and all succeeded.
```

로컬 보존 파일 `image-build-final.log`:

```text
NOTE: Tasks Summary: Attempted 4128 tasks of which 4113 didn't need to be rerun and all succeeded.
```

최초 rootfs 실패는 버전 없는 모듈 별칭, 두 번째 실패는 `/etc/shadow` 부재였다. 메타패키지 의존성과 `shadow` 추가 후 성공했다. 실패 로그를 삭제하거나 최종 성공으로 바꾸지 않았다.

## 이미지 검사 관측값

2026-10-29 `inspection/verification.json`과 추출 파일에 남아 있는 결과다.

| 항목 | 결과 |
|---|---|
| 압축 byte 크기 | `40615730` |
| 압축 SHA-256 | `be2a97c59ba7f2c2595130f14de9e09dfcf70ffda0cf3baa9a3d9001e48233eb` |
| 비압축 byte 크기 | `229847040` |
| 비압축 SHA-256 | `ca12e0875eac6a6fff2b4ac19c0be789f46241f210e9a556147e4969ca972ac6` |
| 커널 release | `6.18.33-v8` |
| 모듈 vermagic | `6.18.33-v8 SMP preempt mod_unload modversions aarch64` |
| 실제 모듈 패키지 | `kernel-module-lab-gpio-6.18.33-v8` |

앱 및 모듈 readelf 파일에서 선택한 실제 행:

```text
app-readelf.txt
  Class:                             ELF64
  Machine:                           AArch64
module-readelf.txt
  Class:                             ELF64
  Machine:                           AArch64
```

Host wrapper 모의시험 기록:

```text
test_modprobe_failure (__main__.InitTests) ... ok
test_operation_lock (__main__.InitTests) ... ok
test_partial_refuses_start (__main__.InitTests) ... ok
test_start_idempotent_stop_restart (__main__.InitTests) ... ok
test_status (__main__.InitTests) ... ok
test_timeout (__main__.InitTests) ... ok
Ran 6 tests in 0.415s
OK
```

실제 ARM daemon이나 GPIO 전기 동작을 실행한 시험은 아니다.

## 2026-10-30 재확인 범위

- 실제 압축 WIC를 다시 읽어 SHA-256·40,615,730 bytes를 확인했다.
- bzip2 전체 스트림 해제 검사를 통과했으며 해제 크기는 229,847,040 bytes다. 파일을 SD에 쓰지 않았다.
- 공개 Layer 13개 파일과 현재 활성 Layer의 같은 상대 경로를 byte 비교했다. 다른 실습 Recipe 전체 복제는 하지 않았다.
- 보존된 실제 manifest에 `kernel-module-lab-gpio-6.18.33-v8`, `lab-gpio`, `lab-gpio-test`, `lab-gpio-autostart`, `kmod`, `shadow`, `shadow-base`가 존재한다.
- FAT/RootFS 전체 추출 검사와 bmap mapped-range 검사는 2026-10-29 결과다. 이번에 해당 기록을 대조했으며 새 재빌드 성공으로 표현하지 않는다.

[최종 보고서](../final-uart-gpio8-image.md) · [HW 증거와 한계](07-gpio-image-hardware-20261030.md)
