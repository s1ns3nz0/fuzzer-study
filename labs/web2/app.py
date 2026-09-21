"""Part 1 랩 타겟 — 퍼징 교육용 취약 웹앱.

의도적으로 취약합니다. 127.0.0.1 밖으로 노출하지 마십시오.

교육 설계: 4~7장이 쓰는 신호를 의도적으로 심어두었습니다.
어떤 신호가 어디에 있는지는 SPOILERS.md 참고.
"""

import os
import random
import time
from collections import deque

from flask import Flask, Response, make_response, redirect, request

app = Flask(__name__)

# ── 보정 노브 ────────────────────────────────────────────────
# 랩마다 신호 세기를 바꿔가며 오라클의 한계를 관찰한다.
# 6장: TIMING_DELAY를 줄여 타이밍 오라클이 언제 무너지는지 본다.
# 7장: RATE_LIMIT을 조여 레이트리밋 하의 퍼징을 실습한다.
TIMING_DELAY = float(os.environ.get("TIMING_DELAY", "0.25"))  # 초
TIMING_JITTER = float(os.environ.get("TIMING_JITTER", "0.0"))  # 초, 노이즈 주입용
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "300"))  # 요청 수
RATE_WINDOW = float(os.environ.get("RATE_WINDOW", "10"))  # 초

# ── 상태 ─────────────────────────────────────────────────────
USERS = {"alice": "wonderland", "bob": "builder"}
SESSIONS: dict[str, str] = {}
_hits: dict[str, deque] = {}

SEARCH_INDEX = {
    "invoice": ["invoice-2024-01.pdf", "invoice-2024-02.pdf", "invoice-2024-03.pdf"],
    "report": ["q1-report.docx", "q2-report.docx"],
    "backup": ["nightly-backup.log"],
    "contract": ["msa-draft.pdf"],
}

# 이 이름들만 느리게 응답한다. 본문은 빠른 응답과 완전히 동일하다.
SLOW_NAMES = {"admin", "root", "alice", "svc_deploy"}


# ── 레이트리밋 ───────────────────────────────────────────────
@app.before_request
def rate_limit():
    ip = request.remote_addr or "unknown"
    now = time.monotonic()
    q = _hits.setdefault(ip, deque())
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        retry = int(RATE_WINDOW - (now - q[0])) + 1
        return Response(
            "rate limited\n", status=429, headers={"Retry-After": str(retry)}
        )
    q.append(now)
    return None


# ── 공개 경로 ────────────────────────────────────────────────
@app.get("/")
def index():
    return """<!doctype html><title>Acme Files</title>
<h1>Acme Files</h1>
<ul>
  <li><a href="/search?q=invoice">Search</a></li>
  <li><a href="/login">Login</a></li>
</ul>
"""


@app.get("/search")
def search():
    """응답 크기 오라클용. 히트/미스가 200으로 같고 길이만 다르다."""
    q = request.args.get("q", "")
    hits = SEARCH_INDEX.get(q.lower(), [])
    if not hits:
        return "<h1>Search</h1><p>0 results</p>\n"
    rows = "\n".join(f"  <li>{h}</li>" for h in hits)
    return f"<h1>Search</h1>\n<p>{len(hits)} results</p>\n<ul>\n{rows}\n</ul>\n"


@app.get("/user")
def user_lookup():
    """타이밍 오라클용. 존재하는 계정만 느리다. 본문은 항상 동일."""
    name = request.args.get("name", "")
    if name.lower() in SLOW_NAMES:
        time.sleep(TIMING_DELAY)
    # 지터는 히트/미스 구분 없이 모든 응답에 걸린다.
    # 느린 쪽에만 걸면 신호와 잡음이 같이 움직여 오라클이 무너지지 않는다.
    time.sleep(random.uniform(0, TIMING_JITTER))
    return "<p>If that account exists, a reset link has been sent.</p>\n"


@app.get("/app/<path:rest>")
def soft_404(rest):
    """soft-404 함정. 아무 경로나 200으로 받아준다.

    상태코드만 보는 퍼저는 여기서 수천 건의 거짓 양성을 만든다.
    크기/단어수 필터를 배우게 하는 장치.
    """
    return "<h1>Acme App</h1><p>Loading…</p>\n"


# ── 인증 ─────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """<form method=post>
<input name=username><input name=password type=password><button>go</button>
</form>
"""
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if USERS.get(u) == p:
        token = f"sess-{u}-{random.randrange(10**9):09d}"
        SESSIONS[token] = u
        resp = make_response(redirect("/account"))
        resp.set_cookie("session", token, httponly=True, samesite="Lax")
        return resp
    return Response("invalid credentials\n", status=401)


def current_user():
    return SESSIONS.get(request.cookies.get("session", ""))


@app.get("/account")
def account():
    u = current_user()
    if not u:
        return redirect("/login")
    return f"<h1>Account</h1><p>Signed in as {u}</p>\n"


@app.get("/api/notes")
def notes():
    """인증 상태 퍼징용. 쿠키를 안 들고 오면 401."""
    u = current_user()
    if not u:
        return Response('{"error":"unauthenticated"}\n', status=401,
                        mimetype="application/json")
    return Response(f'{{"owner":"{u}","notes":["todo: rotate keys"]}}\n',
                    mimetype="application/json")


# ── 숨은 경로 (어디서도 링크되지 않음) ───────────────────────
@app.get("/admin-panel")
def admin_panel():
    """존재하지만 금지. 403 vs 404 차이가 곧 오라클."""
    return Response("forbidden\n", status=403)


@app.get("/backup.zip")
def backup():
    """크기 오라클용 대형 응답."""
    return Response(b"PK\x03\x04" + os.urandom(40_000),
                    mimetype="application/zip")


@app.get("/.env.bak")
def env_bak():
    return Response("DB_PASSWORD=hunter2\nAPI_KEY=sk-lab-not-real\n",
                    mimetype="text/plain")


@app.get("/debug")
def debug():
    """헤더 퍼징용. X-Debug 헤더가 없으면 존재 자체를 숨긴다."""
    if request.headers.get("X-Debug", "").lower() not in ("1", "true", "on"):
        return Response("not found\n", status=404)
    return Response(f"routes={len(app.url_map._rules)} delay={TIMING_DELAY}\n",
                    mimetype="text/plain")


@app.errorhandler(404)
def not_found(_):
    return Response("<h1>404 Not Found</h1>\n", status=404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # 컨테이너 내부. 바인딩은 compose가 제한.
