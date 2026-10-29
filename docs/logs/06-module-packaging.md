# 외부 모듈·C 앱 — 빌드·배포 검증 로그

> **실행 기록:** 2026-10-28~29 / 센터 WSL·Windows 공유 폴더·Raspberry Pi UART
>
> **타깃:** Yocto Poky 6.0.4 / Linux `6.18.33-v8` / AArch64
>
> 제공된 CH05·CH06A·CH06 종합·CH06D Markdown의 실제 관찰 출력 중 Yocto 빌드·배포 관련 부분을 발췌했다. 명령은 실행 환경과 함께 정리했으며 아래 결과는 당시 실행 기록이다.

## 1. `do_configure` 오류 해결

**WSL / 기존 Yocto 빌드 환경**

```bash
bitbake chain-lab
```

**수정 전 출력 발췌:**

```text
ERROR: chain-lab-1.0-r0 do_configure: oe_runmake failed
make: *** No rule to make target 'clean'.  Stop.
```

외부 모듈 Makefile에 `clean:` 규칙을 추가한 뒤 같은 Recipe를 다시 빌드했다.

**수정 후 출력 발췌:**

```text
NOTE: recipe chain-lab-1.0-r0: task do_configure: Succeeded
NOTE: recipe chain-lab-1.0-r0: task do_compile: Succeeded
NOTE: Tasks Summary: Attempted 1028 tasks of which 1010 didn't need to be rerun and all succeeded.
```

`thermal-core`도 Makefile `clean` 타깃을 보완했고, 별도의 `do_compile` 오류였던 `no_llseek` 참조를 제거한 뒤 최종 빌드를 완료했다. Task를 기준으로 빌드 규칙 문제와 커널 API 문제를 구분했다.

## 2. 셸 초기화 오류 해결

**WSL / linux-system-programming의 `ch06-character/`**

```bash
bash ch06c-kit/build_yocto.sh
```

**초기 오류:**

```text
.../oe-init-build-env: line 29: BBSERVER: unbound variable
```

스크립트의 `set -u`를 Yocto 초기화 구간에서 해제하고 이후 복원했다. 수정 후 같은 명령의 출력:

```text
NOTE: Tasks Summary: Attempted 1047 tasks of which 1009 didn't need to be rerun and all succeeded.
[PASS] BitBake finished; AArch64 artifacts staged:
... /mnt/c/Users/Public/arm64-share/thermal_core_06c.ko
... /mnt/c/Users/Public/arm64-share/thermal_ioctl_test
```

위 스크립트는 당시 06C 적용 이력이다. 이후 드라이버를 확장한 트리에서는 테스트 앱 Recipe를 별도로 빌드해 과거 패치가 다시 적용되지 않도록 했다.

## 3. 동일한 배포 파일 확인

**WSL / Yocto 환경 활성화 후**, `KO`는 당시 `chain-lab/1.0/sources/chain_lab.ko` 산출물 경로다.

```bash
sha256sum "$KO" /mnt/c/Users/Public/arm64-share/chain_lab.ko
```

**출력 발췌:**

```text
d992949d9086a983bd57bb890f2b6d81bae002317772dc171a7f6579d01369e0  .../sources/chain_lab.ko
d992949d9086a983bd57bb890f2b6d81bae002317772dc171a7f6579d01369e0  /mnt/c/Users/Public/arm64-share/chain_lab.ko
```

**Raspberry Pi UART / HTTP 수신 후**

```bash
sha256sum /tmp/chain_lab.ko
modinfo -F vermagic /tmp/chain_lab.ko
```

**실제 출력:**

```text
d992949d9086a983bd57bb890f2b6d81bae002317772dc171a7f6579d01369e0  /tmp/chain_lab.ko
6.18.33-v8 SMP preempt mod_unload modversions aarch64
```

이 해시는 4자원 버전 `chain_lab.ko` 10,000바이트에 해당한다. 이전 3자원 버전과 구분한 파일 무결성 근거이며 GPIO 모듈의 해시가 아니다.

## 4. ARM64 모듈·앱의 실장비 실행 연결

**WSL / 기존 Yocto 환경에서 06D 모듈 빌드**

```bash
bitbake thermal-core
```

**당시 요약:**

```text
NOTE: Tasks Summary: Attempted 1028 tasks of which 1010 didn't need to be rerun and all succeeded.
```

**WSL / 원본 저장소 루트에서 테스트 앱 빌드**

```bash
bash ch06-character/userspace/build_06d_yocto.sh
```

**출력 발췌:**

```text
NOTE: Tasks Summary: Attempted 933 tasks of which 914 didn't need to be rerun and all succeeded.
[PASS] Yocto ARM64 06D test staged: /mnt/c/Users/Public/arm64-share/thermal_event_test
... ELF 64-bit LSB pie executable, ARM aarch64 ...
```

**Pi UART / 06D 모듈 적재 후 각 프로그램 실행 결과:**

| 명령 | 실제 출력 요약 |
|---|---|
| `/tmp/thermal_event_test; echo "EXIT_CODE=$?"` | `SUMMARY PASS=16 FAIL=0 TOTAL=16/16`, `EXIT_CODE=0` |
| `/tmp/thermal_ioctl_test; echo "EXIT_CODE=$?"` | `SUMMARY: 23/23 PASS, 0 FAIL`, `EXIT_CODE=0` |
| `/tmp/thermal_test; echo "EXIT_CODE=$?"` | `SUMMARY: 19/19 PASS, 0 FAIL`, `EXIT_CODE=0` |

개별 ARM64 바이너리의 타깃 실행 결과이며 GPIO 전용 이미지의 자동 실행 결과와는 구분한다. Recipe·전송·실행의 해석은 [Chapter 6](../06-custom-layer.md)에 정리했다.
