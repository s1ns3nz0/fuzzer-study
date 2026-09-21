# 11. API 오라클 — 스키마 위반·5xx·BOLA

**Part 2 · API 감사**

9장의 스키마 오라클은 강력했지만 한계가 있습니다. **스키마는 "형태"만
검사합니다.** 응답이 올바른 타입인지, 문서화된 코드인지. 하지만
"이 사용자가 이 자원에 접근해도 되는가?"는 스키마에 없습니다.
그건 형태가 아니라 **의미**의 문제이고, API 취약점의 가장 큰 부류입니다.

이 장은 오라클을 세 층위로 정리하며 Part 2 를 닫습니다.
형태 오라클(스키마) → 크래시 오라클(5xx) → 그리고 스키마가 못 보는
의미 오라클(인가).

## 이 장에서 답할 질문

- 5xx 는 왜 항상 버그인가
- 스키마 오라클이 근본적으로 못 잡는 것은 무엇인가
- BOLA(객체 수준 인가 실패)를 어떻게 오라클로 만드는가

## 5요소 위치

이 장이 다루는 요소: **오라클**

## 준비

```bash
cd labs/api
docker compose up -d
curl -s http://127.0.0.1:5005/createdb
```

## 1. 층위 1 — 5xx는 항상 버그

가장 싼 오라클부터. 서버 오류(5xx)는 **입력이 무엇이든** 발생해선 안 됩니다.
클라이언트가 이상한 걸 보내면 4xx(거부)로 답해야지, 500(서버가 터짐)은
안 됩니다. 그래서 5xx 는 스키마와 무관하게 늘 버그입니다 —
3장의 크래시 오라클이 API 로 옮겨온 형태입니다.

Schemathesis 는 이걸 기본으로 검사합니다(9장 실행에 이미 포함).
`server_error` 체크가 5xx 를 전부 실패로 처리합니다.

## 2. 층위 2 — 스키마 계약 (형태)

9장에서 본 것들입니다. 미문서화 Content-Type, 유효요청 거부, 잘못된
Allow 헤더. 이들은 **응답의 형태**가 스키마 선언과 다른 경우입니다.
자동이고, 강력하고, 사람 노동이 안 듭니다.

하지만 형태 오라클에는 구조적 맹점이 있습니다. 다음을 보십시오.

## 3. 스키마가 통과시키는 치명적 버그

VAmPI 의 이메일 변경 엔드포인트를 봅니다. 스펙상 `PUT /users/v1/{username}/email` —
경로의 `{username}` 사용자의 이메일을 바꾸는 것으로 읽힙니다.
`admin` 으로 로그인해 `name1` 의 이메일을 바꿔봅니다.

```bash
B=http://127.0.0.1:5005
TOK=$(curl -s -X POST $B/users/v1/login -H 'Content-Type: application/json' \
      -d '{"username":"admin","password":"pass1"}' | jq -r '.auth_token')
curl -s -o /dev/null -w '%{http_code}\n' -X PUT $B/users/v1/name1/email \
     -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
     -d '{"email":"pwned@evil.com"}'
```

```text
204
```

`204 No Content` — 성공입니다. 스키마 오라클은 여기서 **아무 문제도 못
느낍니다.** 응답 코드도 타입도 전부 계약대로니까요. 그런데 실제로 무엇이
바뀌었는지 봅시다.

```bash
curl -s $B/users/v1/_debug | jq '.users[] | select(.username=="admin" or .username=="name1") | {username, email}'
```

```text
{ "username": "name1", "email": "mail1@mail.com" }        ← 안 바뀜
{ "username": "admin", "email": "pwned@evil.com" }        ← admin 이 바뀜
```

경로는 `name1` 인데 **`admin` 의 이메일이 바뀌었습니다.** 서버가 경로의
`{username}` 을 무시하고 토큰 주인만 수정한 겁니다. 계약(형태)은 완벽히
지켜졌지만, **경로 파라미터가 거짓말**입니다. 형태 오라클로는 절대 못 잡습니다.

## 4. 층위 3 — BOLA를 오라클로

더 나아갑니다. VAmPI 의 비밀번호 변경은 **남의 계정을 실제로 탈취**할 수
있습니다. 이게 BOLA(Broken Object Level Authorization) — OWASP API
Security Top 10 의 1위입니다.

`labs/api/bola_demo.sh` 가 이걸 실증합니다.

```bash
./bola_demo.sh
```

```text
[*] name1 로 로그인해 토큰 확보
    token len=147
[*] BOLA: name1 토큰으로 name2 의 비밀번호를 바꾼다
    HTTP 204 (204 면 변경 성공)
[*] 탈취 확인: name2 를 새 비밀번호로 로그인
    → Successfully logged in.
[+] BOLA 확인됨: 권한 검사가 path 의 username 을 무시한다
```

`name1` 의 토큰으로 `name2` 의 비밀번호를 `hacked` 로 바꿨고, 그 비밀번호로
`name2` 로그인이 됐습니다. **완전한 계정 탈취입니다.**

이 버그의 오라클은 무엇일까요? 형태가 아닙니다 (204는 정상). 5xx 도
아닙니다. 오라클은 **의미 불변식**입니다.

> 사용자 A 의 자격증명으로 사용자 B 의 자원을 변경할 수 있으면 안 된다.

이건 스키마에 없습니다. 사람이 도메인을 이해하고 **직접 정의**해야 합니다.
그리고 이게 3장에서 예고한, 오라클 설계가 가장 어려워지는 지점입니다.

## 5. 오라클의 세 층위

Part 2 를 정리하면 API 오라클은 세 층입니다.

| 층위 | 오라클 | 자동화 | 잡는 것 |
|------|--------|--------|---------|
| 1 | 5xx = 버그 | 완전 자동 | 서버 크래시 |
| 2 | 스키마 계약 | 자동 (스키마에서) | 형태 불일치 |
| 3 | 의미 불변식 (인가·비즈니스 규칙) | **수작업** | BOLA, 권한 상승, 로직 버그 |

위로 갈수록 자동화가 어렵고, 잡는 버그는 치명적입니다. 자동 도구
(Schemathesis)는 1·2층을 공짜로 줍니다. 하지만 감사의 가치가 나오는
3층은 **사람이 도메인을 이해하고 불변식을 써야** 합니다. 도구는 3층을
대신 못 합니다 — 도구는 "무엇이 정상인지"를 모르니까요.

## 6. 데이터 노출: `_debug`

마지막으로 하나. 위 실습 내내 `/users/v1/_debug` 로 전체 사용자의
비밀번호를 평문으로 봤습니다.

```bash
curl -s http://127.0.0.1:5005/users/v1/_debug | jq '.users[0] | {username, password}'
```

```text
{ "username": "name1", "password": "pass1" }
```

디버그 엔드포인트가 인증 없이 모든 자격증명을 유출합니다(Excessive Data
Exposure). 그리고 이건 스키마에 문서화**되어** 있어서, 8장식 스키마 퍼징으로
발견됩니다 — 하지만 "이게 노출되면 안 된다"는 판단은 또 사람 몫입니다.

## Part 2 정리

API 감사를 다섯 요소로 관통했습니다.

- **생성**(8장): 스키마가 곧 문법. 워드리스트 대신 스키마가 입력을 만든다.
- **오라클**(9장): 스키마가 곧 계약. 형태 위반을 자동 검사한다.
- **피드백**(10장): 호출 순서가 입력. 응답을 다음 요청에 되먹인다.
- **오라클, 심화**(11장): 형태 → 크래시 → 의미의 세 층위. 3층은 사람이 쓴다.

Part 1(web2)과 Part 2(API)의 공통점이 보입니다. 도구와 생성기는 달라도,
**가장 가치 있는 버그는 자동 오라클이 못 잡고 사람이 불변식을 써야 하는
그 지점**에 있습니다. Part 3(web3)은 이 통찰을 극단으로 밀어붙입니다 —
스마트컨트랙트 감사는 **거의 전부가 불변식 설계**입니다.

```bash
docker compose down
```

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Schemathesis 4.27.5, curl 8.x, jq 1.x |
| 컨테이너 | Docker 28.4.0, `erev0s/vampi:latest` (ID 0a5a224b6e14) |
| 비고 | BOLA·이메일 데모는 VAmPI 의 `vulnerable:1` 모드에서 재현됩니다. `createdb` 로 초기화 후 실행하십시오. |

## 참고

- OWASP API Security Top 10 (API1: BOLA): <https://owasp.org/API-Security/>
- 의미 불변식 설계의 극단 → [15장](../part3/15-invariant-design.md)
- 오라클 분류의 뿌리 → [3장](../part0/03-oracle-problem.md)
