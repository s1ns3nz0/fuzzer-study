# Part 0 랩 — 장난감 퍼저

2·3장이 쓰는 20여 줄짜리 퍼저. Docker 불필요, Python 3 만 있으면 됩니다.

| 파일 | 무엇 |
|------|------|
| `target.py` | 퍼징 대상 — 계단식 매직바이트 뒤에 버그가 숨음 |
| `fuzz.py` | 5요소를 최소 구현한 퍼저 (blind / coverage 모드) |
| `test_fuzz.py` | 자체 점검 |

## 실행

```bash
cd labs/part0
python3 fuzz.py coverage    # 커버리지 피드백 있음 → 수천 회에 크래시
python3 fuzz.py blind       # 피드백 없음 → 300만 회에도 못 찾음
python3 test_fuzz.py        # 자체 점검
```

씨앗을 바꿔 반복성을 봅니다: `python3 fuzz.py coverage 1`

## 요점

같은 버그, 같은 생성기·변이·오라클. **피드백(커버리지) 하나의 유무**가
"수천 회"와 "사실상 불가능"을 가릅니다. 이게 Part 0 의 핵심이고,
Part 3(web3 invariant/coverage 퍼징)에서 다른 형태로 다시 나옵니다.
