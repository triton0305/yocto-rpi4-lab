# 최종 GPIO WIC 실장비 수락 기록 — 2026-10-30

**HW VERIFIED — 사용자 제공 검증 결과 기준.** Raspberry Pi 4B에서 UART 로그인,
8채널 자동 실행·버튼 독립 토글, 재부팅 후 자동 실행, 정상 stop 및 LED OFF를 확인했다.

## 1. 출처와 판정 범위

출처는 사용자가 2026-10-30 제공한 **「Yocto Raspberry Pi 4B 최종 통합 이미지 — Codex 최종 작업 명세서」 §4.3**이다.
해당 문서는 사용자와 함께 확인한 UART 결과와 육안 관찰을 항목별로 명시한다.
이번 문서 통합 세션에는 UART 세션 원문 전체, 시각별 캡처, 사진, 전기 측정 파일이 첨부되지 않았다.
따라서 아래 문자열은 **제공된 결과 요약의 관측값**이며 새로 실행하거나 복원한 터미널 로그가 아니다.
실행 위치는 사용자 Raspberry Pi UART이고, 날짜 내 정확한 실행 시각은 미제공이다.

대상 산출물은 `yocto-gpio-toggle-image-raspberrypi4-64.rootfs-20261029073227.wic.bz2`.
Host에서 재확인한 압축 이미지 SHA-256:
`be2a97c59ba7f2c2595130f14de9e09dfcf70ffda0cf3baa9a3d9001e48233eb`.
SD에 기록한 이미지와 이 산출물의 대응은 사용자 제공 기록에 근거하며 이번에 SD를 읽거나 비교하지 않았다.

## 2. HW-01~08 증거표

| ID | 결과 | 관측값과 증거 유형 | 확인 범위·남은 근거 |
|---|---|---|---|
| HW-01 | 확인 | 사용자 UART 결과 요약: `root@raspberrypi4-64` 셸, `uname -r = 6.18.33-v8` | 최종 WIC 부팅·UART 암호 로그인. 전체 부팅 원문 미제공 |
| HW-02 | 확인 | 사용자 UART 결과 요약: GPIO 문자장치 8개, 수동 start 없이 8개 모두 `Toggle controller running.` | 자동 실행·노드 확인. Live DT와 각 platform bind 원문은 별도 미확보 |
| HW-03 | 사용자 관찰 | 정상 동작·초기 LED OFF 보고 | 초기 OFF 전용 로그·전압 측정 없음; 전원 인가부터 probe 이전까지의 전기 상태 보증 아님 |
| HW-04~05 | 사용자 관찰 | D0~D7 버튼별 대응 LED 독립 ON/OFF 토글 정상 | 채널별 UART 로그·영상 없음. 지연·bounce 성능 수치 측정 아님 |
| HW-06 | 확인 | 사용자 UART 결과 요약: 8개 모두 `running` | 원본 `lab_gpio_test all toggle status` 결과 |
| HW-07 | 확인 | 사용자 UART 결과 요약: 변경한 root 암호로 재로그인, kernel 일치, 수동 start 없이 8개 running | 재부팅 후 자동 실행 재현. 재부팅 직후 버튼별 토글 재시험 기록은 없음 |
| HW-08 | 확인 | 사용자 UART 결과 요약: 일부 LED ON 상태에서 stop 후 8개 `stopped; LED OFF.`, 후속 status도 stopped. 육안 전체 OFF | 정상 종료와 관찰된 LED OFF. 광학·전기 계측은 없음 |

앱의 8개 기본 장치명은 `/dev/lab_gpio-lab-gpio`, `/dev/lab_gpio-lab-gpio-d1` ~ `-d7`이다.
핀 매핑·극성의 소스 기준과 운영 명령은 [Chapter 7](../07-gpio-toggle-image.md)에 있다.
암호 변경과 재부팅 뒤 로그인 유지 **사실만** 남기며 암호·hash·인증 파일 본문은 공개하지 않는다.

## 3. 과거 GPIO 검증과 구분

- **2026-10-29 GPIO 기능 확인:** 원격 Chapter 7에 기록된 직접 개발 Driver·앱의 8채널 토글 실증이다. 당시 단일 채널 API/selftest/unbind/rebind 관찰 기록도 그 사건에 속한다.
- **2026-10-29 최종 WIC Host 검사:** 빌드·FAT/RootFS·ABI·인증·서비스 구성 검사다. 당시에는 새 WIC의 HW 시험을 수행하지 않았다.
- **2026-10-30 최종 WIC 실장비 확인:** 이 문서의 새 이미지 수락시험이다. 개별 파일 전송 시험과 구분한다.

참조 저장소의 `CH07_VERIFICATION.md`에 남아 있는 과거 미검증 상태를 소급 수정하지 않았다.
이번 기록은 증거가 확보된 범위의 기능 수락이며 차량 양산·표준 인증·하드 실시간 성능 검증이 아니다.

## 4. 근거 확장과 재검사

추후 사용자가 UART 원문을 제공하면 민감정보를 제외하고 실행 시각·이미지 식별·명령·출력의
관계를 추가할 수 있다. 없는 원문·사진·PASS 로그를 만들어 보충하지 않는다.
재검사 명령, SD 대상 확인 및 복구 절차는 [최종 이미지 보고서](../final-uart-gpio8-image.md#사용자-hw-0108-재검사-절차)에 보존했다.
이번 문서 통합 작업에서는 장비 접근·SD 기록·재플래시를 하지 않았다.
