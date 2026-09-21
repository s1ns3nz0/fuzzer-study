# 6. 응답 오라클 — 크기·코드·시간·차분 필터

**Part 1 · web2 감사**

5장에서 워드리스트가 곧 생성기라는 걸 봤습니다. 후보를 만들어 던지는 쪽입니다.
이 장은 반대편입니다. **던진 뒤 무엇을 보고 "찾았다"고 판정할 것인가.**

이게 오라클입니다. 그리고 퍼징에서 가장 자주 틀리는 부분입니다.
생성기는 대충 만들어도 언젠가 정답을 던집니다. 하지만 오라클이 틀리면
정답이 눈앞을 지나가도 못 알아봅니다.

## 이 장에서 답할 질문

- 상태코드만 보면 왜 거짓 양성이 쏟아지는가
- 응답의 어떤 축이 "존재"를 누설하는가 — 코드·크기·단어수·시간
- 신호가 잡음에 묻히면 오라클은 어떻게 무너지고, 어떻게 복구하는가

## 5요소 위치

이 장이 다루는 요소: **오라클**

| 요소 | 이 장에서의 형태 |
|------|------------------|
| 생성 | 5장의 워드리스트를 그대로 씀 |
| 변이 | 없음 (경로 치환만) |
| 오라클 | **응답의 코드·크기·단어수·시간을 신호로 읽는다 — 이 장의 전부** |
| 피드백 | 없음 (필터는 사후 판정이지 다음 입력을 바꾸지 않음) |
| 커버리지 | 없음 (블랙박스) |

## 준비

```bash
cd labs/web2
docker compose up --build -d
curl -s http://127.0.0.1:8080/    # 200 이면 준비 완료
```

!!! danger "실습 범위"
    이 랩의 대상은 방금 본인이 기동한 `127.0.0.1:8080` 컨테이너뿐입니다.
    [범위와 안전](../scope-and-safety.md)을 아직 안 읽었다면 지금 읽으십시오.

## 1. 순진한 오라클: 상태코드

먼저 틀린 방법을 봅니다. "200이면 존재한다"고 믿는 오라클입니다.
타겟에는 `/app/<무엇이든>` 을 전부 200으로 받아주는 경로가 있습니다.
실무의 SPA 라우터나 커스텀 404 페이지가 흔히 이렇습니다 — **soft-404** 라 부릅니다.

```bash
ffuf -w wordlists/teaching.txt:FUZZ \
     -u http://127.0.0.1:8080/app/FUZZ -mc 200 -t 10
```

```text
admin-panel   [Status: 200, Size: 35, Words: 2, Lines: 2, Duration: 7ms]
app           [Status: 200, Size: 35, Words: 2, Lines: 2, Duration: 9ms]
cgi-bin       [Status: 200, Size: 35, Words: 2, Lines: 2, Duration: 8ms]
backup.zip    [Status: 200, Size: 35, Words: 2, Lines: 2, Duration: 10ms]
...
(총 61건 — 워드리스트 전부가 "히트")
```

워드리스트의 **모든** 항목이 200으로 잡혔습니다. 61개 후보, 61개 히트.
오라클이 틀렸다는 가장 명확한 증거입니다. 신호가 없는데 전부 양성이라면,
그건 판정기가 아니라 그냥 통과기입니다.

`Size` 열을 보십시오. 전부 `35` 입니다. 응답이 다 똑같다는 뜻이고,
곧 다음 필터의 실마리입니다.

## 2. 크기 필터로 soft-404 제거

soft-404 응답은 전부 35바이트로 동일합니다. 그 크기를 필터로 걸어냅니다.
`-fs 35` 는 "크기가 35인 응답은 버려라"입니다.

```bash
ffuf -w wordlists/teaching.txt:FUZZ \
     -u http://127.0.0.1:8080/app/FUZZ -mc 200 -fs 35 -t 10
```

```text
(결과 0건)
```

`/app/*` 밑에는 진짜가 하나도 없었습니다. 61건의 히트는 전부 거짓 양성이었고,
크기 오라클 한 줄이 그걸 전부 지웠습니다.

이제 진짜 경로가 있는 루트에서 같은 걸 합니다. 여기선 미존재를 404로 돌려주니
`-fc 404`(404를 필터)로 충분합니다.

```bash
ffuf -w wordlists/teaching.txt:FUZZ \
     -u http://127.0.0.1:8080/FUZZ -mc all -fc 404 -t 10
```

```text
admin-panel   [Status: 403, Size: 10,    Words: 1,  Lines: 2]
backup.zip    [Status: 200, Size: 40004, Words: 172, Lines: 133]
.env.bak      [Status: 200, Size: 44,    Words: 1,  Lines: 3]
login         [Status: 200, Size: 103,   Words: 5,  Lines: 4]
search        [Status: 200, Size: 32,    Words: 2,  Lines: 2]
user          [Status: 200, Size: 59,    Words: 10, Lines: 2]
```

여섯 개가 남았습니다. 주목할 두 가지:

- `/admin-panel` 은 **403**입니다. "접근 금지"는 "없음"과 다릅니다.
  403은 그 자리에 뭔가 있다는 강한 누설입니다 — 코드 자체가 오라클입니다.
- `/backup.zip` 은 40KB입니다. 나머지와 자릿수가 다릅니다.
  크기는 존재뿐 아니라 **가치**도 누설합니다.

## 3. 상태코드도 크기도 같을 때: 차분

여기서부터가 진짜입니다. `/search?q=` 는 히트든 미스든 **전부 200**이고,
본문 구조도 같습니다. 다른 건 오직 길이뿐입니다.

미스의 크기를 먼저 재둡니다.

```bash
curl -s -o /dev/null -w 'miss size=%{size_download}\n' \
     "http://127.0.0.1:8080/search?q=zzz"
```

```text
miss size=32
```

미스는 32바이트. 그러니 32를 걸어내면 히트만 남습니다.

```bash
ffuf -w wordlists/terms.txt:FUZZ \
     -u "http://127.0.0.1:8080/search?q=FUZZ" -mc 200 -fs 32 -t 10
```

```text
invoice    [Status: 200, Size: 137, Words: 8, Lines: 8]
report     [Status: 200, Size: 96,  Words: 6, Lines: 7]
backup     [Status: 200, Size: 74,  Words: 4, Lines: 6]
contract   [Status: 200, Size: 69,  Words: 4, Lines: 6]
```

20개 검색어 중 네 개가 히트입니다. 상태코드는 20개 다 200이었습니다.
코드만 봤다면 아무것도 못 건졌습니다. **차분 — 미스 기준선과의 차이 — 이 오라클입니다.**

!!! tip "크기 대신 단어수"
    응답에 타임스탬프나 랜덤 토큰이 섞이면 크기가 요청마다 흔들립니다.
    그럴 땐 `-fs` 대신 `-fw`(단어수)나 `-fl`(줄수)가 안정적입니다.
    위 출력의 `Words`·`Lines` 열이 그래서 있습니다.

## 4. 응답에 아무 차이도 없을 때: 시간

마지막 관문. `/user?name=` 은 존재하는 계정이든 아니든
**상태코드·크기·단어수·본문이 전부 동일**합니다.

```bash
curl -s -o /dev/null -w 'size=%{size_download} time=%{time_total}s\n' \
     "http://127.0.0.1:8080/user?name=admin"
curl -s -o /dev/null -w 'size=%{size_download} time=%{time_total}s\n' \
     "http://127.0.0.1:8080/user?name=nobody"
```

```text
size=59 time=0.255s    ← admin (존재)
size=59 time=0.005s    ← nobody (미존재)
```

크기 59로 같고, **시간만 다릅니다.** 존재하는 계정을 조회할 때
서버가 뭔가 더 하기 때문입니다 (실무에선 해시 비교, DB 조회 같은 것).
ffuf 의 `-mt`(match time)로 느린 응답만 잡습니다. `>100` 은 100ms 초과.

```bash
ffuf -w wordlists/usernames.txt:FUZZ \
     -u "http://127.0.0.1:8080/user?name=FUZZ" \
     -mc 200 -mt ">100" -mmode and -t 1
```

```text
admin        [Status: 200, Size: 59, Duration: 253ms]  ◀
alice        [Status: 200, Size: 59, Duration: 253ms]  ◀
root         [Status: 200, Size: 59, Duration: 253ms]  ◀
svc_deploy   [Status: 200, Size: 59, Duration: 254ms]  ◀
```

!!! warning "-mt 는 매처, -ft 는 필터"
    `-mt`(match)는 "이 시간인 것만 남겨라", `-ft`(filter)는 "이 시간인 걸 버려라"입니다.
    타이밍 신호를 **찾을** 때는 `-mt` 입니다. `-t 1` 로 동시성을 1로 낮춘 것도 중요합니다 —
    병렬 요청은 서로의 응답 시간을 밀어내 측정을 흐립니다.

계정 4개가 잡혔습니다. 응답이 완전히 동일한데도, **시간이라는 축 하나만으로**
존재하는 사용자명을 열거했습니다. 이게 타이밍 오라클입니다.

## 5. 오라클은 언제 무너지는가

여기까지는 신호가 깨끗했습니다. 현실은 안 그렇습니다.
서버 지연은 GC, 네트워크, 이웃 부하로 요청마다 출렁입니다.
이 잡음을 랩에서 재현합니다 — `TIMING_JITTER` 로 모든 응답에
0~200ms 무작위 지연을 주입하고, 진짜 신호(`TIMING_DELAY`)는 50ms로 줄입니다.
이제 잡음(200ms)이 신호(50ms)보다 큽니다.

```bash
TIMING_DELAY=0.05 TIMING_JITTER=0.20 docker compose up -d --force-recreate
```

같은 명령을 다시 돌립니다.

```bash
ffuf -w wordlists/usernames.txt:FUZZ \
     -u "http://127.0.0.1:8080/user?name=FUZZ" \
     -mc 200 -mt ">100" -mmode and -t 1
```

```text
alice        [Status: 200, Duration: 145ms]  ◀ (진짜)
carol        [Status: 200, Duration: 120ms]  ◀ 거짓 양성
deploy       [Status: 200, Duration: 203ms]  ◀ 거짓 양성
jenkins      [Status: 200, Duration: 167ms]  ◀ 거짓 양성
root         [Status: 200, Duration: 205ms]  ◀ (진짜)
svc_deploy   [Status: 200, Duration: 233ms]  ◀ (진짜)
sysadmin     [Status: 200, Duration: 172ms]  ◀ 거짓 양성
ubuntu       [Status: 200, Duration: 127ms]  ◀ 거짓 양성
```

정답은 `admin alice root svc_deploy` 넷입니다. 그런데 결과엔
가짜 넷이 섞여 들어왔고(`carol`, `deploy`…), 진짜인 `admin` 은 그 한 번의
측정에서 운 나쁘게 100ms를 못 넘겨 빠졌습니다. **오라클이 무너졌습니다.**

무너진 이유는 명확합니다. `ffuf` 는 후보당 한 번만 쏩니다.
잡음이 신호보다 크면, 그 한 번의 측정이 곧 판정이 되어버립니다.
단일 표본으로는 100ms 지연과 우연히 느린 요청을 구별할 수 없습니다.

## 6. 오라클 복구: 반복 표본

처방은 통계입니다. 후보마다 한 번이 아니라 여러 번 쏘고 중앙값을 씁니다.
잡음은 평균으로 깎이고, 진짜 지연은 매번 있으니 남습니다.
`ffuf` 로는 안 되니 작은 스크립트를 씁니다 (`labs/web2/timing_probe.py`).

임계값은 고정하지 않습니다. 측정값을 정렬한 뒤 **가장 큰 간격**에서 자릅니다 —
신호가 있으면 분포가 느린 덩어리와 빠른 덩어리로 갈리고, 그 사이가 최대 간격이 됩니다.

후보당 9회부터.

```bash
python3 timing_probe.py wordlists/usernames.txt 9
```

```text
표본 9회 · 최대 간격 12.9ms (상위 14개에서 갈림)

  admin          154.9ms  ◀ 히트
  root           146.9ms  ◀ 히트
  administrator  138.0ms  ◀ 히트   ← 거짓 양성
  ubuntu         135.6ms  ◀ 히트   ← 거짓 양성
  ...
```

아직 부족합니다. 9회로는 덩어리가 안 갈려 컷이 엉뚱한 데 섰습니다.
표본을 101회로 올립니다.

```bash
python3 timing_probe.py wordlists/usernames.txt 101
```

```text
표본 101회 · 최대 간격 19.7ms (상위 4개에서 갈림)

  svc_deploy   162.2ms  ◀ 히트
  alice        157.6ms  ◀ 히트
  admin        154.0ms  ◀ 히트
  root         149.6ms  ◀ 히트
  deploy       129.9ms
  carol        124.9ms
  ...
```

정확히 네 개. 거짓 양성도 없고 `admin` 도 돌아왔습니다.
신호는 그대로였는데 표본이 부족했을 뿐입니다.

!!! note "측정기 자신의 잡음"
    처음엔 `urllib` 로 요청마다 새 TCP 연결을 열었더니, macOS Docker 에서
    핸드셰이크 편차가 타겟 지연보다 커져 표본을 아무리 늘려도 안 갈렸습니다.
    연결을 재사용(keep-alive)하도록 바꾸고 나서야 신호가 드러났습니다.
    **오라클을 의심하기 전에 측정기부터 의심하십시오.**
    `timing_probe.py` 가 `http.client` 연결을 재사용하는 이유입니다.

## 정리

오라클은 단일한 것이 아니라 **누설 축의 사다리**입니다.

| 축 | 언제 쓰나 | ffuf |
|----|-----------|------|
| 상태코드 | 미존재가 404/403으로 갈릴 때 | `-mc` / `-fc` |
| 크기 | 코드는 같고 본문 길이가 다를 때 | `-fs` / `-mode` |
| 단어수·줄수 | 크기가 노이즈로 흔들릴 때 | `-fw` / `-fl` |
| 시간 | 응답이 전부 동일할 때 | `-mt` / `-ft` |
| 반복 표본 | 잡음이 신호보다 클 때 | (스크립트) |

위로 갈수록 신호가 약하고 잡음에 취약합니다. 감사에서 헛발질하는 대부분은
생성기가 나빠서가 아니라 **한 칸 아래 축에서 멈췄기** 때문입니다.
soft-404 를 코드로만 보다 놓치고, 사용자 열거를 크기로만 보다 놓칩니다.

Part 2 에서 오라클은 다시 등장합니다. 거기선 응답의 크기나 시간이 아니라
**API 스키마 위반**이 신호가 됩니다. 축이 바뀔 뿐, "무엇을 버그라 부를 것인가"라는
질문은 같습니다.

```bash
docker compose down    # 실습 종료
```

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 모든 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | ffuf 2.3.0 (Homebrew), curl 8.x, Python 3.12.11 |
| 컨테이너 | Docker 28.4.0, `labs/web2` (Flask 3.1.0) |
| 비고 | 타이밍 절대값(ms)은 하드웨어·부하에 따라 다릅니다. 재현되는 것은 히트/미스의 **상대적 분리**입니다. |

## 참고

- ffuf 필터·매처 옵션: `ffuf -h`
- 이 타겟의 신호 설계 의도: `labs/web2/SPOILERS.md` (실습 후 열람)
- 타이밍 사이드채널 일반론 → 15장(web3 불변식)에서 다른 형태로 재등장
