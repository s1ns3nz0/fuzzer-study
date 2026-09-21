# Part 2 랩 — API 타겟 (VAmPI)

8~11장이 쓰는 취약 API. 기성 교육용 이미지 `erev0s/vampi` 를 씁니다.

!!! VAmPI 는 의도적으로 취약합니다. `127.0.0.1:5005` 에만 바인딩됩니다.

## 기동

```bash
docker compose up -d
curl -s http://127.0.0.1:5005/ | jq .
curl -s http://127.0.0.1:5005/createdb    # 테스트 데이터 채우기 (실습 전 필수)
docker compose down                        # 실습 후
```

## 도구 (격리 venv)

```bash
python3 -m venv .venv
.venv/bin/pip install schemathesis==4.27.5
.venv/bin/schemathesis run http://127.0.0.1:5005/openapi.json --url http://127.0.0.1:5005
```

`.venv/` 는 `.gitignore` 에 들어 있습니다.

## 파일

| 파일 | 무엇 | 장 |
|------|------|-----|
| `docker-compose.yml` | VAmPI 기동 | 8–11 |
| `bola_demo.sh` | BOLA 계정 탈취 재현 | 11 |

## 요점

- 스키마가 생성기(8장)이자 오라클(9장)이다.
- 호출 순서가 입력공간의 한 축이다(10장).
- 자동 오라클은 형태·크래시를 잡지만, BOLA 같은 의미 버그는 사람이
  불변식을 써야 한다(11장).
