# Part 1 랩 — web2 타겟

4~7장이 쓰는 취약 웹앱. 교육 목적으로 직접 만든 것입니다.

!!! 이 컨테이너는 의도적으로 취약합니다. 인터넷에 노출하지 마십시오.

## 기동

```bash
docker compose up --build -d
curl -s http://127.0.0.1:8080/
docker compose down   # 실습 후
```

`127.0.0.1` 에만 바인딩되어 있습니다.

## 보정 노브

장마다 신호 세기를 바꿔가며 오라클이 언제 무너지는지 관찰합니다.

| 환경변수 | 기본값 | 쓰는 곳 |
|----------|--------|---------|
| `TIMING_DELAY` | `0.25` | 6장 — 타이밍 오라클 한계 관찰 |
| `TIMING_JITTER` | `0.0` | 6장 — 노이즈 주입 |
| `RATE_LIMIT` | `300` | 7장 — 레이트리밋 하의 퍼징 |
| `RATE_WINDOW` | `10` | 7장 |

```bash
TIMING_DELAY=0.02 RATE_LIMIT=20 docker compose up --build -d
```

## 워드리스트

`wordlists/teaching.txt` — 60여 항목. SecLists 없이도 5장 실습이 돌아가도록
히트와 미스를 섞어 만든 교육용 목록입니다.

## 자체 점검

심어둔 신호가 살아있는지 확인합니다. 본문이 이 신호들에 의존하므로,
앱을 수정했다면 반드시 돌리십시오.

```bash
pip install -r requirements.txt
python test_target.py
```

## 설계 의도

어떤 신호를 어디에 심었는지는 [SPOILERS.md](SPOILERS.md) 에 있습니다.
실습 전에는 열지 마십시오.
