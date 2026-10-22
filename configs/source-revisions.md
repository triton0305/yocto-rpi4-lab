# Yocto 소스 버전 관리

## 개발 환경

| 항목 | 설정 |
|---|---|
| Yocto Project | 6.0.4 (wrynose) |
| Distribution | poky |
| Machine | raspberrypi4-64 |
| Host | WSL2 Ubuntu (x86-64) |

## 소스 리비전

학교와 집에서 동일한 Yocto 개발 환경을 재현하기 위해 각 Git 저장소의 커밋 ID를 기록한다.

| Repository | Git Commit |
|---|---|
| BitBake | `3ccdabf1ba2b65dde0025ad04f84b80c02a1fd6e` |
| OpenEmbedded-Core | `636e5d3b12d54951c13d57346648bc29a0e6b24e` |
| meta-raspberrypi | `919588393f41b48cb6c5d832aa35e58a19b6762d` |
| meta-yocto | `실제 명령 출력값 입력` |

## 빌드 구성

```conf
MACHINE = "raspberrypi4-64"
DISTRO = "poky"

BB_NUMBER_THREADS = "4"
PARALLEL_MAKE = "-j 4"
```

## 저장소 관리 원칙

- 외부 Yocto 소스는 별도 디렉터리에서 관리한다.
- 직접 작성한 Layer, Recipe, Application은 `yocto-rpi4-lab`에서 관리한다.
- Git Commit ID를 이용해 동일한 소스 버전을 재현한다.
- 빌드 결과물과 캐시는 GitHub에 업로드하지 않는다.
- 개발 환경 재구성 시 Yocto 설정과 필요한 Host 패키지도 별도로 확인한다.

