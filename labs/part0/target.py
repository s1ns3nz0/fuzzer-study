"""퍼징 대상 — 계단식 매직바이트 뒤에 버그가 숨은 파서.

blind 퍼징으로는 사실상 도달 불가능하고(4바이트를 정확히 맞춰야 함),
커버리지 피드백이 있으면 한 바이트씩 진전해 뚫린다.
2·3장이 이 대비를 실증한다.
"""


def process(data: bytes) -> str:
    """마법값 b'FUZZ' 로 시작하고 다섯 번째 바이트가 0x42면 크래시.

    각 매칭 단계가 새로운 코드 경로(라인)를 연다. 그래서 커버리지를
    보는 퍼저는 "한 글자 더 맞은" 입력을 진전으로 인식하고 보존한다.
    """
    if len(data) < 1 or data[0:1] != b"F":
        return "reject: byte0"
    if len(data) < 2 or data[1:2] != b"U":
        return "reject: byte1"
    if len(data) < 3 or data[2:3] != b"Z":
        return "reject: byte2"
    if len(data) < 4 or data[3:4] != b"Z":
        return "reject: byte3"
    if len(data) < 5:
        return "reject: too short"
    if data[4] == 0x42:  # 'B'
        raise AssertionError("crash: FUZZ + 0x42 reached")
    return "ok: deep path, no crash"
