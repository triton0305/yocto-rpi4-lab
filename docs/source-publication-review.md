# 소스 구성·로컬 인증·이미지 재현

직접 개발한 GPIO Driver·C 애플리케이션을 Yocto 이미지에 통합하는 Layer와 도구를 설명한다.
[Chapter 7](07-gpio-toggle-image.md)은 통합 구조를, [최종 보고서](final-uart-gpio8-image.md)는
이미지 식별·Host 검사·HW 수락 결과를 다룬다.

## 소스 구성

`layers/meta-yocto-lab`의 13개 파일은 실제 빌드에 사용한 활성 Layer와 byte 동일성을 확인했다.
Driver·App·UAPI·Makefile은 고정 GPIO SHA의 사본이며, 활성 DTS는 8개 status를 `okay`로 만든 별도 파일이다.
기준 revision은 [소스 리비전](../configs/source-revisions.md)에 기록한다.

| 파일 | 역할 |
|---|---|
| [conf/layer.conf](../layers/meta-yocto-lab/conf/layer.conf) | Recipe 검색 경로·wrynose 호환성 |
| [lab-gpio_1.0.bb](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/lab-gpio_1.0.bb) | 모듈 빌드·패키징 |
| [driver/lab_gpio.c](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/driver/lab_gpio.c) | 직접 개발한 GPIO Platform Driver |
| [driver/Makefile](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/driver/Makefile) | 외부 모듈 Kbuild 연결 |
| [driver UAPI](../layers/meta-yocto-lab/recipes-kernel/lab-gpio/files/include/lab_gpio_uapi.h) | 커널·앱 공통 API |
| [lab-gpio-test_1.0.bb](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/lab-gpio-test_1.0.bb) | C 앱 교차 컴파일·설치 |
| [lab_gpio_test.c](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/files/lab_gpio_test.c) | 직접 개발한 8채널 토글 앱 |
| [app UAPI](../layers/meta-yocto-lab/recipes-apps/lab-gpio-test/files/lab_gpio_uapi.h) | driver UAPI와 byte 동일 |
| [lab-gpio-overlay_1.0.bb](../layers/meta-yocto-lab/recipes-bsp/lab-gpio-overlay/lab-gpio-overlay_1.0.bb) | DT Overlay 빌드·deploy |
| [활성 8채널 DTS](../layers/meta-yocto-lab/recipes-bsp/lab-gpio-overlay/files/lab-gpio-eight-overlay.dts) | 실제 이미지의 노드·GPIO offset·극성 |
| [lab-gpio-autostart_1.0.bb](../layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/lab-gpio-autostart_1.0.bb) | SysV 서비스 패키지 |
| [lab-gpio-init](../layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/files/lab-gpio-init) | 모듈 적재·장치 대기·앱 시작/중지/상태 확인 |
| [yocto-gpio-toggle-image.bb](../layers/meta-yocto-lab/recipes-core/images/yocto-gpio-toggle-image.bb) | 패키지·FAT 부팅 파일·인증 정책 |

| 도구·문서 | 용도 |
|---|---|
| [prepare-gpio-credentials.py](../scripts/prepare-gpio-credentials.py) | 개발자별 초기 root 암호·hash를 로컬에 생성 |
| [sync-gpio-layer.py](../scripts/sync-gpio-layer.py) | 기존 활성 Layer에 통합 파일 동기화, 변경 파일 백업 |
| [verify-gpio-wic.py](../scripts/verify-gpio-wic.py) | 실제 WIC의 FAT/RootFS·ABI·manifest·인증·init 구성 검사 |
| [test_gpio_init.py](../tests/test_gpio_init.py) | 임시 mock 환경에서 init wrapper 상태·실패 경로 검사 |
| [.gitignore](../.gitignore) | 이미지·인증 파일·캐시·로컬 검사 결과 제외 |
| [최종 보고서](final-uart-gpio8-image.md) | 빌드·실패 복구·산출물·기록/복구 절차 |
| [Host 증거](logs/07-gpio-image-host.md) | 실제 빌드·검사 파일의 최소 발췌 |
| [HW 수락 기록](logs/07-gpio-image-hardware-20261030.md) | 사용자 UART 결과 요약·육안 관찰·확인 범위 |

센터의 활성 Layer에는 다른 실습 Recipe도 있다. 이 저장소의 GPIO Layer 파일만 동기화하고,
전체 Layer를 덮어쓰거나 BBLAYERS에 두 벌을 등록하지 않는다. 과거 개별 모듈 성과는
[Chapter 6](06-custom-layer.md)과 기존 로그·고정 소스 링크에서 추적한다.

## 인증 도구의 동작과 사용 조건

도구 소스에는 실제 비밀번호·hash·token이 없다. `secrets.token_urlsafe(18)`로 개발자별 값을 만들고,
암호는 명령행 인수가 아닌 stdin으로 `openssl passwd -6`에 전달한다.
출력에는 파일 보관 위치만 표시하고 암호·hash 값은 표시하지 않는다.
생성 위치는 지정한 build의 `conf/gpio-private/`이며 디렉터리 0700, 파일 0600을 사용한다.
기존 파일이 있으면 중단하며 `O_EXCL`로 덮어쓰기를 방지한다.

이 도구는 **개발자 개인 소유의 신뢰할 수 있는 빌드 디렉터리**에서 사용한다.
기존 디렉터리 symlink·소유권 확인은 도구 자체에 없으므로 아래 사전 검사를 거친다.
다른 사용자가 쓰기 가능한 공유 경로에서는 실행하지 않는다.
두 파일은 순서대로 생성하므로 저장 공간·파일 쓰기 실패 시 일부만 남을 수 있다.
그 경우 자동 재시도로 덮어쓰지 않고 아래 실패 처리 절차를 따른다.

Image Recipe는 `${TOPDIR}/conf/gpio-private/root-password.hash`를 읽어 root 인증을 설정한다.
`root-password.txt`는 해당 이미지를 새로 기록했을 때의 초기 로그인 정보이며 빌드에는 hash만 필요하다.
검사 도구는 이 두 로컬 파일을 사용해 이미지 속 root hash와 초기 암호의 대응을 확인한다.
실장비에서 변경한 암호는 초기 파일과 별도로 관리한다.

## 인증 생성 절차

필수 도구는 Python 3 표준 라이브러리와 SHA-512 crypt를 지원하는 `openssl passwd -6`이다.
저장소 루트에서 실행하고 `GPIO_BUILD_DIR`은 본인의 기존 Yocto build 절대 경로로 지정한다.
인증 파일이 이미 있으면 이 절차를 반복하지 않고 기존 보관 정보를 사용한다.
새 개발자는 기존 사용자의 인증 파일 대신 아래 절차로 자신의 값을 생성한다.

아래 사전 검사는 build부터 파일시스템 루트까지 symlink·다른 사용자의 쓰기 권한을 검사하고,
build/conf의 소유권과 인증 경로의 부재를 확인한다. 실패하면 생성 도구를 실행하지 않는다.
신뢰할 수 없는 프로세스가 경로를 동시에 바꾸는 환경까지 방어하는 도구는 아니다.

```sh
GPIO_BUILD_DIR="$HOME/study/rootfs/yocto/bitbake-builds/poky-wrynose/build"
if python3 - "$GPIO_BUILD_DIR" <<'PY'
import os
from pathlib import Path
import stat
import sys

build = Path(sys.argv[1]).expanduser().absolute()
for path in (build, *build.parents, build / 'conf'):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o022:
        raise SystemExit('Use real directories without group/other write access.')
    if info.st_uid not in (0, os.getuid()):
        raise SystemExit('An ancestor is owned by another user.')
for path in (build, build / 'conf'):
    if path.stat().st_uid != os.getuid():
        raise SystemExit('Build and conf must belong to the current user.')
if os.path.lexists(build / 'conf/gpio-private'):
    raise SystemExit('Credentials path exists; preserve and inspect it privately.')
print('Credential path checks passed.')
PY
then
    python3 scripts/prepare-gpio-credentials.py "$GPIO_BUILD_DIR"
else
    echo 'Credential preparation stopped; review the path before retrying.' >&2
fi
```

생성 후 권한은 값을 출력하지 않는 다음 명령으로 확인한다.

```sh
stat -c '%a %U %n' \
  "$GPIO_BUILD_DIR/conf/gpio-private" \
  "$GPIO_BUILD_DIR/conf/gpio-private/root-password.txt" \
  "$GPIO_BUILD_DIR/conf/gpio-private/root-password.hash"
```

디렉터리 700·파일 600과 본인 소유인지 확인한다. 초기 암호는 개인 로컬 편집기로 확인하며
터미널 녹화·화면 공유·로그 수집 환경에서는 열지 않는다. 비밀번호·hash·shadow 본문을 문서나 이슈에 붙이지 않는다.

생성 중 실패해 파일 하나만 남으면 해당 디렉터리를 0700이 유지되는 로컬 비공개 백업 위치에 보존한다.
완료된 빌드에서 사용한 자격 정보와 구분하고, 기존 경로의 처리·보관 여부를 사용자가 판단한 뒤
인증 경로가 없는 상태에서 새로 생성한다. 기존 쌍을 임의로 한 파일씩 교체하지 않는다.
새 인증정보로 재빌드한 이미지는 이전 결과와 SHA-256이 달라질 수 있으며 별도 HW 수락시험 대상이다.

## 빌드·검사 흐름

1. [환경 구성](01-environment.md)과 [소스 리비전](../configs/source-revisions.md)에 맞는 Yocto checkout을 준비한다.
2. 아래 두 방식 중 환경에 맞는 **하나만** 선택한다. 이미 활성 `meta-yocto-lab`이 있으면 기존 Layer를 유지하며 통합 파일을 동기화한다. 없는 신규 환경에서는 이 저장소의 Layer를 직접 등록한다.
3. 위 인증 절차를 한 번 완료한다. 값은 BitBake 명령이나 shell 변수에 넣지 않는다.
4. [최종 보고서의 재현 명령](final-uart-gpio8-image.md#재현)으로 구성 Recipe와 이미지를 빌드한다.
5. 같은 보고서의 WIC 검사 명령으로 실제 이미지 내부를 확인한다. 검사는 native 도구·pkgdata·커널 산출물이 있는 해당 Yocto build를 사용한다.

### 신규 환경의 Layer 등록

아직 활성 `meta-yocto-lab`이 없는 환경에서만 저장소의 Layer를 직접 등록한다.
`GPIO_BUILD_DIR`은 위에서 확인한 build 경로이고, 아래 명령의 시작 위치는 저장소 루트다.

```sh
GPIO_REPO_DIR="$PWD"
source "$GPIO_BUILD_DIR/init-build-env"
bitbake-layers show-layers
# 위 목록에 meta-yocto-lab이 없을 때만 실행한다.
bitbake-layers add-layer "$GPIO_REPO_DIR/layers/meta-yocto-lab"
bitbake-layers show-layers
cd "$GPIO_REPO_DIR"
```

이미 활성 Layer가 있으면 직접 등록하는 명령을 실행하지 않는다.
[최종 보고서의 기존 환경 절차](final-uart-gpio8-image.md#재현)에 따라 `sync-gpio-layer.py`를 사용한다.
신규 환경에서 직접 등록한 경우에는 해당 동기화 명령을 건너뛴다. 두 방식 모두 인증 준비 후
같은 네 구성 Recipe와 `yocto-gpio-toggle-image`를 빌드한다.

검사 output은 `.local-artifacts/` 아래처럼 공개 제외된 개인 경로를 사용한다.
추출한 RootFS·전체 WIC에는 인증 hash가 포함된다. 검사 결과 JSON이 암호를 출력하지 않는다는 사실과
RootFS 추출 파일 자체의 민감성을 구별한다.

## 저장소에서 제외하는 산출물

[.gitignore](../.gitignore)는 WIC/IMG 및 압축본, 생성 모듈·DTB/DTBO, 비공개 인증 디렉터리와 파일,
로컬 환경 비밀 파일, Yocto tmp/downloads/sstate 캐시, Python 캐시, 로컬 검사·백업 경로를 제외한다.
검증 로그의 안전한 발췌와 SHA-256은 Markdown 문서로 관리한다.
ignore 규칙은 이미 추적 중인 파일을 제거하지 않으므로 Git 반영 전 파일 목록과 diff도 확인한다.

기존 Chapter와 원문 로그의 Host 경로·명령은 당시 실행 근거로 보존한다.
2026-10-29 Host 빌드·검사와 2026-10-30 HW 수락 결과는 [최종 보고서](final-uart-gpio8-image.md)에서
날짜·근거 유형을 구분한다. 재현 절차를 보완했다고 새 BitBake 빌드나 새 실장비 시험을 수행한 것으로 간주하지 않는다.
