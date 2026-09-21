"""20여 줄 장난감 퍼저 — 퍼징의 5요소를 최소한으로 구현.

    python fuzz.py blind      # 커버리지 피드백 없음
    python fuzz.py coverage   # 커버리지 피드백 있음

두 모드가 같은 버그(target.process)를 찾는 데 걸리는 실행 횟수를 비교한다.
"""

import random
import sys

from target import process

MAX_EXEC = 3_000_000


# ── 커버리지 (5요소: 커버리지) ────────────────────────────────
def run_with_coverage(data: bytes):
    """process(data) 를 돌리며 밟은 줄 번호 집합을 함께 반환한다."""
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


# ── 변이 (5요소: 변이) ────────────────────────────────────────
def mutate(data: bytes) -> bytes:
    if not data:
        return bytes([random.randrange(256)])
    b = bytearray(data)
    op = random.random()
    if op < 0.5:  # 바이트 뒤집기
        i = random.randrange(len(b))
        b[i] = random.randrange(256)
    elif op < 0.8:  # 뒤에 붙이기
        b.append(random.randrange(256))
    else:  # 잘라내기
        i = random.randrange(len(b))
        del b[i]
    return bytes(b)


def fuzz(mode: str) -> int:
    # 생성 (5요소: 생성) — 씨앗 코퍼스
    corpus: list[bytes] = [b""]
    seen_coverage: set = set()

    for n in range(1, MAX_EXEC + 1):
        # 생성: 코퍼스에서 하나 골라 변이
        data = mutate(random.choice(corpus))

        crashed, cov = run_with_coverage(data)

        # 오라클 (5요소: 오라클) — 예외 발생이 곧 버그
        if crashed:
            return n

        # 피드백 (5요소: 피드백) — coverage 모드만 코퍼스를 늘린다
        if mode == "coverage" and cov not in seen_coverage:
            seen_coverage.add(cov)
            corpus.append(data)

    return -1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "coverage"
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    n = fuzz(mode)
    if n < 0:
        print(f"[{mode}] {MAX_EXEC}회 안에 크래시 못 찾음")
    else:
        print(f"[{mode}] {n}회 만에 크래시 발견")
