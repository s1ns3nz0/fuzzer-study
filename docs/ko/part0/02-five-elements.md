# 2. 퍼징의 5요소 — 생성·변이·오라클·피드백·커버리지

**Part 0 · 퍼징의 뼈대**

1장에서 퍼징을 정의했습니다. 이 장은 그 정의를 **작동하는 코드**로 만듭니다.
20여 줄짜리 Python 퍼저를 세우고, 그것을 다섯 부품으로 분해합니다.
이 다섯 부품이 이 교재가 세 도메인을 관통하는 격자입니다.

## 이 장에서 답할 질문

- 퍼저를 이루는 다섯 부품은 각각 무슨 일을 하는가
- 그중 "피드백"은 왜 결정적인가 — 있고 없고가 얼마나 차이 나는가

## 5요소

| 요소 | 하는 일 | 이 장의 코드 |
|------|---------|--------------|
| **생성** | 입력을 어디서 가져오나 | 코퍼스에서 하나 고름 |
| **변이** | 가진 입력을 어떻게 비트나 | 바이트 뒤집기·추가·삭제 |
| **오라클** | 무엇을 버그라 부르나 | 예외 발생 = 버그 |
| **피드백** | 결과로 다음을 바꾸나 | 새 커버리지 → 코퍼스에 보존 |
| **커버리지** | 얼마나 봤는지 어떻게 아나 | 밟은 줄 번호 집합 |

## 준비

```bash
cd labs/part0
python3 --version    # 3.10 이상
```

Docker 도 외부 라이브러리도 필요 없습니다. 표준 라이브러리만 씁니다.

## 1. 커버리지 — 프로그램이 흘리는 신호

먼저 "얼마나 봤나"를 재는 부품입니다. Python 의 `sys.settrace` 로
`process()` 가 실행 중 밟은 줄 번호를 모읍니다 (`fuzz.py`).

```python
def run_with_coverage(data: bytes):
    lines: set[int] = set()

    def tracer(frame, event, arg):
        if event == "line" and frame.f_code.co_name == "process":
            lines.add(frame.f_lineno)
        return tracer

    crashed = False
    sys.settrace(tracer)
    try:
        process(data)
    except AssertionError:
        crashed = True
    finally:
        sys.settrace(None)
    return crashed, frozenset(lines)
```

이게 커버리지 계측입니다. 실무 퍼저(AFL++, libFuzzer)는 컴파일 시점에
바이너리에 계측을 심어 훨씬 빠르게 같은 일을 합니다. 원리는 동일합니다 —
**어느 코드가 실행됐는지 기록한다.**

## 2. 변이 — 입력을 비틀기

가진 입력을 조금씩 바꿉니다. 세 가지 연산: 바이트 뒤집기, 뒤에 붙이기, 잘라내기.

```python
def mutate(data: bytes) -> bytes:
    if not data:
        return bytes([random.randrange(256)])
    b = bytearray(data)
    op = random.random()
    if op < 0.5:                       # 바이트 뒤집기
        i = random.randrange(len(b))
        b[i] = random.randrange(256)
    elif op < 0.8:                     # 뒤에 붙이기
        b.append(random.randrange(256))
    else:                             # 잘라내기
        i = random.randrange(len(b))
        del b[i]
    return bytes(b)
```

이게 변이입니다. 무에서 입력을 만드는 게 아니라(그건 생성),
**있는 입력을 재료로** 이웃 입력을 만듭니다.

## 3. 루프 — 다섯 요소가 맞물리는 곳

이제 조립합니다. 이 루프가 퍼저의 심장입니다.

```python
def fuzz(mode: str) -> int:
    corpus: list[bytes] = [b""]        # 생성: 씨앗 코퍼스
    seen_coverage: set = set()

    for n in range(1, MAX_EXEC + 1):
        data = mutate(random.choice(corpus))   # 생성 + 변이
        crashed, cov = run_with_coverage(data) # 커버리지

        if crashed:                            # 오라클
            return n

        if mode == "coverage" and cov not in seen_coverage:  # 피드백
            seen_coverage.add(cov)
            corpus.append(data)                # 새 경로 연 입력을 보존

        # mode == "blind" 이면 이 피드백 블록이 통째로 빠진다
    return -1
```

다섯 요소가 한눈에 보입니다.

- **생성**: `random.choice(corpus)` — 코퍼스에서 하나 고른다
- **변이**: `mutate(...)` — 골라온 것을 비튼다
- **커버리지**: `run_with_coverage` — 밟은 줄을 잰다
- **오라클**: `if crashed` — 예외면 버그
- **피드백**: `if cov not in seen_coverage` — 새 경로를 연 입력을 코퍼스에 넣는다

**blind 모드와 coverage 모드의 유일한 차이는 마지막 피드백 블록뿐입니다.**
생성기도 변이도 오라클도 똑같습니다. 이제 그 한 블록이 얼마나 차이를 내는지 봅니다.

## 4. 실측: 피드백이 있고 없고

1장의 버그(`FUZZ` + `0x42`)를 두 모드로 찾게 합니다.

```bash
python3 fuzz.py coverage 0
python3 fuzz.py coverage 1
python3 fuzz.py coverage 2
python3 fuzz.py blind 0
```

```text
[coverage] 18915회 만에 크래시 발견
[coverage] 5288회 만에 크래시 발견
[coverage] 12523회 만에 크래시 발견
[blind] 3000000회 안에 크래시 못 찾음
```

커버리지 모드는 5천~1만9천 회에 찾았습니다. blind 모드는 **300만 회에도
못 찾았습니다.** 같은 생성기, 같은 변이, 같은 오라클. 차이는 피드백 블록
다섯 줄뿐입니다.

## 5. 왜 이렇게까지 차이 나는가

피드백이 하는 일을 실행 중에 들여다봅니다. 코퍼스가 언제 자라는지 찍어보면:

```text
크래시 @ 5288회, 코퍼스 크기=7
  실행      1: 코퍼스 2개, 새 경로 연 입력 = b' '
  실행    912: 코퍼스 3개, 새 경로 연 입력 = b'F'
  실행   2295: 코퍼스 4개, 새 경로 연 입력 = b'FU'
  실행   4460: 코퍼스 5개, 새 경로 연 입력 = b'FUZ'
  실행   4743: 코퍼스 6개, 새 경로 연 입력 = b'FUZZ'
  실행   4830: 코퍼스 7개, 새 경로 연 입력 = b'FUZZ8'
```

퍼저가 계단을 **한 칸씩** 올랐습니다. `F` 를 맞히면 `data[1:2]` 검사 줄에
처음 도달합니다 — 새 커버리지입니다. 그래서 `b'F'` 가 코퍼스에 보존되고,
다음부터는 그걸 변이해 `FU` 를 노립니다. `FU` 가 또 새 줄을 열고… 이렇게
`F → FU → FUZ → FUZZ` 로 진전합니다.

핵심은 **부분 진전이 보상받는다**는 점입니다. blind 모드는 `FUZZ` 를 통째로
맞히기 전까지 아무 보상이 없습니다 — `F` 만 맞은 입력과 아무것도 못 맞은
입력이 동등하게 버려집니다. 그래서 43억분의 1을 정면으로 뚫어야 합니다.
커버리지는 이 확률을 네 개의 작은 확률(각 1/256)로 쪼갭니다.

> 커버리지 피드백의 본질: **입력공간의 거리를, 프로그램이 흘리는 신호로 근사한다.**
> "얼마나 가까운지"를 알 수 있으면, 먼 거리도 가까운 걸음의 연속이 된다.

## 정리

- 퍼저 = 생성 · 변이 · 오라클 · 피드백 · 커버리지, 다섯 부품.
- 앞의 셋만으로도 퍼저는 돈다 (blind). 하지만 깊은 버그엔 못 닿는다.
- 피드백(커버리지)이 부분 진전을 보상해, 넘을 수 없는 확률을 계단으로 만든다.
- 실측: 같은 버그를 커버리지는 수천 회에, blind 는 300만 회에도 못 찾았다.

다음 장(3장)은 이 퍼저의 한 부품을 정면으로 다룹니다 — **오라클**.
지금은 "예외 = 버그"로 단순했지만, 실제로 "무엇을 버그라 부를 것인가"는
퍼징에서 가장 어려운 질문입니다.

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 모든 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Python 3.12.11 (표준 라이브러리만) |
| 랩 | `labs/part0` (`target.py`, `fuzz.py`) |
| 비고 | 실행 횟수는 씨앗값에 따라 다릅니다. 재현되는 것은 "coverage 는 수천 회, blind 는 300만 회에도 실패"라는 자릿수 차이입니다. |

## 참고

- 자체 점검: `python3 labs/part0/test_fuzz.py`
- 커버리지 가이드 퍼징의 실전 도구: AFL++, libFuzzer (원리 동일, 계측이 컴파일 시점)
- 오라클을 정면으로 → [3장](03-oracle-problem.md)
- 이 커버리지 아이디어의 web3 판 → [14장](../part3/14-invariant-handlers.md)
