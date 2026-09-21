# 퍼징으로 읽는 보안 감사

입력공간 탐색이라는 하나의 뼈대로 web2 · API · web3 감사를 관통하는 한국어 퍼징 교재.

> **상태: 집필 중.** 16개 장의 골격과 인프라만 서 있습니다.
> 사이트 배포는 전 장이 작성·검증을 마친 뒤에 수동으로 트리거합니다.

## 구성

| Part | 장 | 랩 타겟 |
|------|-----|---------|
| 0 · 퍼징의 뼈대 | 1–3 | 장난감 퍼저 (Python) |
| 1 · web2 감사 | 4–7 | `labs/web2` — 자체 제작 취약 앱 |
| 2 · API 감사 | 8–11 | `labs/api` — VAmPI |
| 3 · web3 감사 | 12–15 | `labs/web3` — damn-vulnerable-defi + anvil |
| 4 · 회고 | 16 | — |

## 로컬에서 보기

```bash
pip install -r requirements.txt
mkdocs serve
```

`http://127.0.0.1:8000` 에서 열립니다.

## 원칙

**실행 증거 의무.** 교재에 실리는 모든 명령어는 실제로 랩 환경에서 실행되어
출력이 확인된 것만 게재합니다. 각 장 하단 「검증 로그」에 검증 일자·도구 버전·
환경이 기록되며, 미검증 장은 상단에 경고 배너가 붙습니다.

**로컬 타겟 한정.** 모든 실습 대상은 독자가 직접 기동하는 컨테이너입니다.
자세한 내용은 [범위와 안전](docs/ko/scope-and-safety.md).

## 구조

```
docs/ko/          본문 (영문판은 docs/en/ 을 추가하면 구조 변경 없이 붙는다)
labs/             파트별 docker-compose 실습 환경
mkdocs.yml        사이트 설정 및 네비게이션
```

## 라이선스

- 본문: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ko)
- 코드 및 랩: [MIT](LICENSE)
