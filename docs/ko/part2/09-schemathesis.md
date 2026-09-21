# 9. Schemathesis — 속성 기반 API 테스팅

**Part 2 · API 감사**

8장에서 스키마를 생성기로 썼습니다. 이 장은 스키마의 반대편 얼굴 —
**오라클**을 켭니다. 3장에서 오라클의 한 종류로 "불변식"을 소개했습니다:
레퍼런스 없이, 항상 참이어야 할 성질을 검사하는 것. Schemathesis 가
하는 일이 정확히 이겁니다. **API 응답이 늘 만족해야 할 성질을 스키마에서
자동으로 뽑아 검사합니다.**

## 이 장에서 답할 질문

- 스키마에서 어떤 "항상 참인 성질"을 뽑아낼 수 있는가
- Schemathesis 가 자동으로 켜는 검사(check)는 무엇인가
- VAmPI 는 그 계약을 실제로 어디서 어기는가

## 5요소 위치

이 장이 다루는 요소: **생성 + 오라클**

| 요소 | 이 장에서의 형태 |
|------|------------------|
| 생성 | 8장의 스키마 기반 생성 |
| 오라클 | **응답이 스키마 계약을 만족하는지 검사 — 이 장의 전부** |

## 준비

```bash
cd labs/api
docker compose up -d
curl -s http://127.0.0.1:5005/createdb    # 테스트 데이터 채우기
```

## 1. 속성 기반 테스팅이란

보통의 테스트는 예시 기반입니다. "입력 3을 주면 출력 9가 나와야 한다"처럼
구체적 입출력 쌍을 사람이 씁니다. **속성 기반**(property-based)은 다릅니다.
구체적 값 대신 **모든 입력에 대해 참이어야 할 성질**을 씁니다.

- 예시 기반: `abs(-7) == 7`
- 속성 기반: `모든 x 에 대해 abs(x) >= 0`

3장의 불변식 오라클이 이거였습니다. Schemathesis 는 이 아이디어를 API 에
적용합니다. 그런데 성질을 사람이 안 씁니다 — **스키마에서 자동으로 뽑습니다.**

## 2. 스키마에서 뽑히는 성질들

OpenAPI 스키마는 응답에 대해 여러 약속을 담고 있습니다. 각 약속이 곧
"항상 참이어야 할 성질"입니다.

| 스키마가 선언한 것 | 뽑히는 성질 (오라클) |
|--------------------|----------------------|
| 응답 Content-Type: `application/json` | 응답은 늘 그 타입이어야 한다 |
| 응답 본문 스키마 | 본문은 그 구조를 만족해야 한다 |
| 정의된 상태코드 목록 | 문서에 없는 코드는 안 나와야 한다 |
| 유효한 요청 정의 | 스키마 유효 요청을 서버가 거부하면 안 된다 |
| 서버는 크래시하면 안 된다 | 5xx 는 늘 버그다 |

이 성질들을 사람이 한 줄도 안 썼습니다. 스키마에 이미 있던 선언을
뒤집었을 뿐입니다.

## 3. 실행과 결과

전체를 돌립니다.

```bash
.venv/bin/schemathesis run http://127.0.0.1:5005/openapi.json \
  --url http://127.0.0.1:5005 --max-examples 20
```

요약 부분:

```text
Test Phases:
  ❌ Examples
  ❌ Coverage
  ❌ Fuzzing
  ❌ Stateful

Failures:
  ❌ API rejected schema-compliant request: 4
  ❌ Invalid Allow header: 3
  ❌ Undocumented Content-Type: 6

Test cases:
  326 generated, 13 found 13 unique failures
```

세 종류의 계약 위반이 나왔습니다. 하나씩 봅니다.

## 4. 위반 1: 미문서화 Content-Type

가장 많이(6건) 나온 위반입니다. 한 오퍼레이션만 좁혀 상세를 봅니다.

```bash
.venv/bin/schemathesis run http://127.0.0.1:5005/openapi.json \
  --url http://127.0.0.1:5005 \
  --include-path '/books/v1/{book_title}' --include-method GET --max-examples 5
```

```text
=================================== FAILURES ===================================
__________________________ GET /books/v1/{book_title} __________________________
- Undocumented Content-Type

    Received:   application/problem+json
    Documented: application/json

[401] Unauthorized:
    { "detail": "Invalid authorization header", "status": 401, ... }

Reproduce with:
    curl -X GET -H 'Authorization: [Filtered]' http://127.0.0.1:5005/books/v1/bookTitle77
```

스키마는 이 엔드포인트가 `application/json` 을 반환한다고 선언했습니다.
그런데 인증 실패 시 `application/problem+json` 을 반환합니다.
**선언과 실제가 다릅니다.** 사소해 보이지만, 이건 클라이언트가 응답을
파싱하다 깨질 수 있는 실제 계약 위반입니다 — 그리고 사람이 이 검사를
따로 작성하지 않았는데 오라클이 잡았습니다.

## 5. 위반 2: 스키마 유효 요청을 거부

스키마가 "이렇게 보내면 유효하다"고 정의한 요청을, 서버가 거부했습니다
(4건). 두 방향 중 하나입니다 — 스키마가 실제보다 느슨하거나(문서 오류),
서버가 유효 입력을 잘못 처리하거나(구현 버그). 어느 쪽이든 **스키마와
구현이 어긋났다**는 신호이고, 감사에서 파고들 지점입니다.

## 6. 위반 3: 잘못된 Allow 헤더

허용되지 않은 메서드에 서버는 `405` 와 함께 `Allow` 헤더로 "이 경로는
GET, POST 를 허용한다"를 알려야 합니다(HTTP 표준). VAmPI 의 `Allow`
헤더가 규격에 안 맞았습니다(3건). 이것도 사람이 안 짠 검사입니다 —
Schemathesis 가 HTTP 표준 자체를 오라클로 들고 있습니다.

## 7. 인증 경고를 읽는 법

실행 끝에 경고가 있었습니다.

```text
⚠️ Missing authentication: 6 operations returned only 401/403 responses
```

여섯 개 오퍼레이션이 **전부 401/403** 만 돌려줬습니다. 인증이 필요한데
Schemathesis 가 토큰 없이 두드렸기 때문입니다. 7장에서 배운 것과 같습니다 —
**인증 뒤 표면은 인증을 들고 들어가야 보입니다.** 토큰 없이 돌린 이 여섯
오퍼레이션의 결과는 사실상 "401 벽"만 확인한 것입니다.

그 벽 너머에 VAmPI 의 진짜 취약점이 있습니다. 다음 두 장이 그리로 갑니다 —
10장은 인증 상태를 시퀀스로 잇고, 11장은 그 상태로 인가 버그를 찾습니다.

## 정리

- 속성 기반 테스팅은 구체적 입출력 대신 "늘 참일 성질"을 검사한다.
- Schemathesis 는 그 성질을 스키마에서 자동으로 뽑는다 — 사람이 안 쓴다.
- VAmPI 는 3종 계약을 어겼다: 미문서화 Content-Type, 유효요청 거부, 잘못된 Allow.
- 토큰 없이 돌리면 인증 뒤 표면은 401 벽만 확인된다 (10·11장에서 넘어간다).

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Schemathesis 4.27.5 |
| 컨테이너 | Docker 28.4.0, `erev0s/vampi:latest` (ID 0a5a224b6e14) |
| 비고 | 실패 건수·분류는 씨앗과 `--max-examples` 에 따라 달라집니다. 재현되는 것은 세 종류의 계약 위반이 존재한다는 사실입니다. |

## 참고

- Schemathesis checks: <https://schemathesis.readthedocs.io/>
- 속성 기반 테스팅(Hypothesis): <https://hypothesis.readthedocs.io/>
- 오라클 분류 복습 → [3장](../part0/03-oracle-problem.md)
- 인증 상태를 시퀀스로 → [10장](10-stateful-sequences.md)
