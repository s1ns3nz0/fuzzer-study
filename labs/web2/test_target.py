"""심어둔 신호가 실제로 존재하는지 확인하는 자체 점검.

4~7장 수업이 이 신호들에 의존한다. 여기가 깨지면 본문이 거짓말이 된다.

    python test_target.py
"""

import time

from app import TIMING_DELAY, app

c = app.test_client()


def test_status_oracle():
    """숨은 경로는 존재 여부가 상태코드로 샌다."""
    assert c.get("/admin-panel").status_code == 403
    assert c.get("/nope-does-not-exist").status_code == 404
    assert c.get("/backup.zip").status_code == 200


def test_size_oracle():
    """검색 히트/미스가 둘 다 200이고 길이만 다르다."""
    hit = c.get("/search?q=invoice")
    miss = c.get("/search?q=zzzznope")
    assert hit.status_code == miss.status_code == 200
    assert len(hit.data) > len(miss.data) * 2, "크기 차이가 너무 작다"


def test_soft_404_trap():
    """/app/* 는 아무 경로나 200 + 동일 본문. 상태코드 오라클을 무력화한다."""
    a = c.get("/app/anything")
    b = c.get("/app/totally-different")
    assert a.status_code == b.status_code == 200
    assert a.data == b.data, "함정이 되려면 본문이 동일해야 한다"


def test_timing_oracle():
    """존재하는 계정만 느리다. 본문은 구별 불가."""
    t0 = time.monotonic()
    slow = c.get("/user?name=admin")
    slow_dt = time.monotonic() - t0

    t0 = time.monotonic()
    fast = c.get("/user?name=nobody-here")
    fast_dt = time.monotonic() - t0

    assert slow.data == fast.data, "타이밍 말고 다른 신호가 새고 있다"
    assert slow_dt > fast_dt + TIMING_DELAY / 2, "지연 신호가 관측되지 않는다"


def test_header_gated_route():
    """X-Debug 없으면 존재 자체가 404로 숨는다."""
    assert c.get("/debug").status_code == 404
    assert c.get("/debug", headers={"X-Debug": "1"}).status_code == 200


def test_auth_gate():
    """쿠키 없는 퍼징은 401 벽에 막힌다 (7장)."""
    assert c.get("/api/notes").status_code == 401
    r = c.post("/login", data={"username": "alice", "password": "wonderland"})
    assert r.status_code == 302
    ok = c.get("/api/notes")
    assert ok.status_code == 200 and b"alice" in ok.data


def test_rate_limit():
    """레이트리밋이 실제로 429를 낸다 (7장)."""
    import app as target

    saved = target.RATE_LIMIT
    target.RATE_LIMIT = 5
    target._hits.clear()
    try:
        codes = [c.get("/").status_code for _ in range(8)]
        assert 429 in codes, f"429가 안 나왔다: {codes}"
    finally:
        target.RATE_LIMIT = saved
        target._hits.clear()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\n심어둔 신호 전부 확인됨")
