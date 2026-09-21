# 8. 스키마가 곧 문법 — OpenAPI를 생성기로

**Part 2 · API 감사**

Part 1 에서 생성기는 워드리스트였습니다. 사람이 손으로 모은 단어 목록을
경로에 하나씩 끼워 던졌습니다. API 는 다릅니다. **API 는 자기 입력공간을
스스로 문서화합니다** — OpenAPI(구 Swagger) 스키마로. 이 장은 그 스키마를
퍼징의 생성기로 삼는 법을 봅니다.

## 이 장에서 답할 질문

- OpenAPI 스키마는 입력공간의 무엇을 말해주는가
- 스키마가 어떻게 "문법"으로서 입력을 생성하는가
- 워드리스트 방식과 무엇이 근본적으로 다른가

## 5요소 위치

이 장이 다루는 요소: **생성**

| 요소 | 이 장에서의 형태 |
|------|------------------|
| 생성 | **OpenAPI 스키마가 유효한 요청의 문법이 된다 — 이 장의 전부** |
| 변이 | 스키마가 허용하는 범위 안팎으로 값을 흔든다 (9장) |
| 오라클 | 스키마 위반 = 버그 (9장) |
| 피드백 | 상태 링크로 시퀀스를 잇는다 (10장) |
| 커버리지 | 오퍼레이션·상태코드 커버리지 |

## 준비

```bash
cd labs/api
docker compose up -d          # VAmPI 기동 (erev0s/vampi)
curl -s http://127.0.0.1:5005/ | jq .
```

```json
{ "message": "VAmPI the Vulnerable API", "vulnerable": 1 }
```

!!! danger "실습 범위"
    VAmPI 는 의도적으로 취약한 API 이며, `127.0.0.1:5005` 에만 바인딩됩니다.
    [범위와 안전](../scope-and-safety.md).

Part 2 의 랩 도구(Schemathesis)는 격리 venv 에 둡니다.

```bash
python3 -m venv .venv
.venv/bin/pip install schemathesis==4.27.5
```

## 1. API 는 입력공간을 스스로 말한다

VAmPI 의 OpenAPI 스키마를 가져옵니다.

```bash
curl -s http://127.0.0.1:5005/openapi.json | jq '{openapi, title:.info.title, paths:(.paths|keys)}'
```

```json
{
  "openapi": "3.0.1",
  "title": "VAmPI",
  "paths": [
    "/", "/books/v1", "/books/v1/{book_title}", "/createdb",
    "/me", "/users/v1", "/users/v1/_debug", "/users/v1/login",
    "/users/v1/register", "/users/v1/{username}",
    "/users/v1/{username}/email", "/users/v1/{username}/password"
  ]
}
```

Part 1 에서는 이 경로 목록을 **워드리스트로 추측해서** 찾아야 했습니다.
API 는 그냥 알려줍니다. 경로뿐이 아닙니다 — 각 경로가 받는 메서드,
파라미터, 요청 본문의 형태, 응답의 형태까지 전부 스키마에 있습니다.
`email` 변경 엔드포인트를 봅시다.

```bash
curl -s http://127.0.0.1:5005/openapi.json \
  | jq '.paths."/users/v1/{username}/email".put.requestBody.content'
```

```json
{
  "application/json": {
    "schema": {
      "type": "object",
      "properties": { "email": { "type": "string", "example": "mail3@mail.com" } }
    }
  }
}
```

스키마가 말합니다. "이 엔드포인트는 PUT 이고, `email`(문자열) 필드를 가진
JSON 객체를 받는다." **이게 유효한 입력의 문법입니다.**

## 2. 문법에서 입력을 생성한다

문법이 있으면 그 문법을 만족하는 문장을 무한히 만들 수 있습니다.
Schemathesis 가 이걸 합니다 — 스키마를 읽고, 각 필드 타입에 맞는 값을
[Hypothesis](https://hypothesis.readthedocs.io/) 로 생성합니다.
`email: string` 이면 온갖 문자열을, 정수 필드면 경계값(0, -1, 최대값)을,
enum 이면 각 항목을.

한 번 돌려보고 규모만 확인합니다 (자세한 해석은 9장).

```bash
.venv/bin/schemathesis run http://127.0.0.1:5005/openapi.json \
  --url http://127.0.0.1:5005 --max-examples 20 2>&1 | grep -A3 'Test cases:'
```

```text
Test cases:
  326 generated, 13 found 13 unique failures
```

14개 오퍼레이션에서 **326개의 테스트 케이스가 자동 생성**됐습니다.
사람이 워드리스트를 모으지 않았습니다. 스키마가 곧 생성기였습니다.

## 3. 워드리스트 생성 vs 스키마 생성

두 방식의 차이는 근본적입니다.

| | 워드리스트 (Part 1) | 스키마 (Part 2) |
|--|--------------------|-----------------| 
| 입력공간을 아는 법 | 추측 (없는 건 못 찾음) | 선언되어 있음 |
| 생성 단위 | 경로 문자열 | 구조화된 요청 (경로+메서드+본문+타입) |
| 유효성 | 대부분 404 (틀린 추측) | 대부분 스키마 유효 |
| 강점 | 문서에 없는 숨은 경로 | 문서화된 표면의 깊은 검증 |

중요한 건 **둘이 상호보완**이라는 점입니다. 스키마 퍼징은 문서화된 표면을
깊게 팝니다. 하지만 스키마에 없는 엔드포인트(`_debug` 같은 디버그 경로가
스펙에서 빠져 있다면)는 못 봅니다. 실무에서는 스키마 퍼징으로 문서화된
표면을 훑고, Part 1 식 경로 퍼징으로 문서 밖을 훑습니다.

!!! tip "스키마가 없으면"
    OpenAPI 스펙을 제공하지 않는 API 도 많습니다. 그럴 땐 트래픽을 관찰해
    스펙을 역생성(mitmproxy2swagger 등)하거나, 손으로 최소 스펙을 씁니다.
    스키마 퍼징의 전제는 "문법이 있다"이고, 문법을 확보하는 것부터가 일입니다.

## 4. 스키마의 두 얼굴: 생성기이자 오라클

이 장은 스키마를 **생성기**로 썼습니다. 하지만 스키마에는 응답의 형태도
적혀 있습니다 — 어떤 상태코드, 어떤 Content-Type, 어떤 본문 구조가
"정상"인지. 그 선언을 뒤집으면 **오라클**이 됩니다. "응답이 스키마에
선언된 형태와 다르면 버그다."

이게 Part 2 를 Part 1 과 가르는 지점입니다. Part 1 의 오라클은 우리가
바깥에서 관찰해 만든 것(크기 차분, 타이밍)이었습니다. Part 2 의 오라클은
**API 가 스스로 약속한 계약**입니다. 다음 장에서 그 계약을 어떻게
자동으로 검사하는지, 그리고 VAmPI 가 그 계약을 어떻게 어기는지 봅니다.

## 정리

- API 는 입력공간을 OpenAPI 스키마로 스스로 문서화한다.
- 스키마는 유효한 요청의 **문법**이고, 그 문법에서 입력을 무한 생성할 수 있다.
- Schemathesis 는 14개 오퍼레이션에서 326개 케이스를 자동 생성했다 — 워드리스트 없이.
- 스키마는 생성기이자 오라클이다. 응답 형태 선언을 뒤집으면 계약 검사가 된다.

다음 장(9장)은 그 오라클을 켭니다. 스키마가 약속한 계약을 VAmPI 가 어디서
어기는지 — 실제 실패 13건을 해석합니다.

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Schemathesis 4.27.5, jq 1.x |
| 컨테이너 | Docker 28.4.0, `erev0s/vampi:latest` (ID 0a5a224b6e14) |
| 비고 | 생성 케이스 수(326)와 실패 수는 씨앗·`--max-examples` 에 따라 다릅니다. |

## 참고

- OpenAPI 3 스펙: <https://spec.openapis.org/oas/v3.0.1>
- Schemathesis: <https://schemathesis.readthedocs.io/>
- 스키마를 오라클로 → [9장](09-schemathesis.md)
