"""장난감 퍼저 자체 점검. 본문이 이 동작에 의존한다.

    python test_fuzz.py
"""

from fuzz import fuzz, run_with_coverage
from target import process


def test_crash_reproduces():
    """알려진 크래시 입력이 실제로 크래시한다."""
    crashed, _ = run_with_coverage(b"FUZZ\x42")
    assert crashed


def test_deep_path_no_crash():
    """마법값은 맞지만 트리거 바이트가 다르면 크래시 안 함."""
    crashed, _ = run_with_coverage(b"FUZZ\x00")
    assert not crashed
    assert process(b"FUZZ\x00") == "ok: deep path, no crash"


def test_coverage_grows_on_progress():
    """한 글자 더 맞은 입력은 더 많은 줄을 밟는다 (피드백의 근거)."""
    _, cov_none = run_with_coverage(b"XXXX")
    _, cov_two = run_with_coverage(b"FUXX")
    assert len(cov_two) > len(cov_none)


def test_coverage_mode_beats_blind():
    """커버리지 모드는 blind 가 못 뚫는 걸 뚫는다."""
    n = fuzz("coverage")
    assert n > 0, "coverage 모드가 크래시를 못 찾았다"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\n장난감 퍼저 동작 확인됨")
