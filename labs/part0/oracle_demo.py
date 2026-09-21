"""오라클의 종류를 보여주는 데모 (3장).

같은 버그를, 크래시 오라클은 못 보고 차분 오라클은 본다.

    python oracle_demo.py
"""


def my_abs(x: int) -> int:
    """절댓값 — 인데 x = -7 에서 조용히 틀린다 (크래시 없음)."""
    if x == -7:
        return -7  # 버그: 음수를 그대로 반환. 예외는 안 난다.
    return x if x >= 0 else -x


def ref_abs(x: int) -> int:
    """신뢰하는 레퍼런스 구현."""
    return abs(x)


def crash_oracle(lo: int, hi: int) -> list[int]:
    """예외가 난 입력만 버그로 본다."""
    bugs = []
    for x in range(lo, hi):
        try:
            my_abs(x)
        except Exception:
            bugs.append(x)
    return bugs


def differential_oracle(lo: int, hi: int) -> list[int]:
    """레퍼런스와 답이 다른 입력을 버그로 본다."""
    return [x for x in range(lo, hi) if my_abs(x) != ref_abs(x)]


if __name__ == "__main__":
    lo, hi = -100, 101
    crash = crash_oracle(lo, hi)
    diff = differential_oracle(lo, hi)
    print(f"크래시 오라클: {len(crash)}건 발견")
    print(f"차분 오라클:   {len(diff)}건 발견 → x={diff}")
    assert crash == [], "이 버그는 크래시가 아니어야 한다 (데모의 전제)"
    assert diff == [-7], "차분 오라클은 x=-7 을 잡아야 한다"
    print("\n같은 버그, 다른 오라클 — 크래시만 보면 놓친다")
