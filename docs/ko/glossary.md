# 용어집

이 교재에 나오는 용어를 한곳에 모았습니다. 처음 보는 용어를 만나면
여기서 찾으십시오. 정의는 이 교재의 맥락(퍼징)에 맞춘 것이며, 각 항목
끝의 장 번호는 그 용어를 처음/자세히 다루는 곳입니다.

## 퍼징의 뼈대

입력공간 (input space)
: 어떤 프로그램이 받을 수 있는 모든 입력의 집합. 대개 너무 커서 전부
  시험할 수 없다. 퍼징의 출발점. → [1장](part0/01-what-is-fuzzing.md)

퍼징 (fuzzing)
: 너무 커서 다 볼 수 없는 입력공간을, 유한한 시간 안에, 버그가 있을 법한
  쪽으로 편향되게 탐색하는 일. → [1장](part0/01-what-is-fuzzing.md)

blind 퍼징
: 피드백 없이 무작위로 입력을 던지는 방식. 깊은 곳에 숨은 버그에는
  사실상 도달하지 못한다. → [2장](part0/02-five-elements.md)

생성 (generation)
: 5요소의 하나. 입력을 어디서 가져오는가. 워드리스트·스키마·함수
  시그니처 등이 생성기가 된다. → [2장](part0/02-five-elements.md)

변이 (mutation)
: 5요소의 하나. 가진 입력을 비틀어 이웃 입력을 만드는 것 (바이트 뒤집기·
  추가·삭제 등). → [2장](part0/02-five-elements.md)

오라클 (oracle)
: 5요소의 하나. "무엇을 버그라 부를 것인가"를 판정하는 부품. 퍼징에서
  가장 어렵고 중요한 요소. → [3장](part0/03-oracle-problem.md)

피드백 (feedback)
: 5요소의 하나. 한 실행의 결과로 다음 입력을 바꾸는 것. 커버리지·상태
  누적·데이터 의존 등의 형태. → [2장](part0/02-five-elements.md)

커버리지 (coverage)
: 5요소의 하나. 프로그램의 어느 부분이 실행됐는지의 척도 (밟은 코드 줄 등).
  피드백의 흔한 신호원. → [2장](part0/02-five-elements.md)

코퍼스 (corpus)
: 퍼저가 보존하는 "흥미로운 입력"들의 모음. 커버리지 퍼징은 새 경로를 연
  입력을 코퍼스에 넣고, 그걸 변이해 다음 입력을 만든다. → [2장](part0/02-five-elements.md)

씨앗 (seed)
: (1) 코퍼스의 초기 입력. (2) 난수 생성기의 초기값 — 같은 씨앗은 같은
  퍼징 결과를 재현한다. → [2장](part0/02-five-elements.md)

## 오라클의 종류

크래시 오라클 (crash oracle)
: 예외·패닉·세그폴트가 나면 버그로 보는 오라클. 가장 싸지만 조용한 논리
  버그를 놓친다. → [3장](part0/03-oracle-problem.md)

차분 오라클 (differential oracle)
: 두 구현의 답을 비교해 다르면 버그로 보는 오라클. 레퍼런스가 있을 때
  강력하다. web2 의 응답 크기 차분도 이 부류. → [3장](part0/03-oracle-problem.md)

불변식 (invariant)
: 프로그램이 어떤 입력·상태에서도 항상 참이어야 하는 성질. 이것을 오라클로
  쓰면 레퍼런스 없이 버그를 잡는다. web3 감사의 핵심. → [3장](part0/03-oracle-problem.md), [15장](part3/15-invariant-design.md)

속성 기반 테스팅 (property-based testing)
: 구체적 입출력 쌍 대신 "모든 입력에 참이어야 할 성질"을 검사하는 테스트
  방식. Schemathesis·forge fuzz 가 이 방식. → [9장](part2/09-schemathesis.md)

거짓 양성 / 거짓 음성 (false positive / false negative)
: 거짓 양성은 정상을 버그라 잘못 신고, 거짓 음성은 진짜 버그를 놓침.
  오라클 설계는 이 둘의 균형이다. → [3장](part0/03-oracle-problem.md)

## web2

워드리스트 (wordlist)
: 경로·파라미터·계정명 후보를 모은 단어 목록. web2 퍼징의 생성기.
  목록에 없는 것은 못 찾는다. → [5장](part1/05-ffuf-wordlist.md)

ffuf
: web2 경로·파라미터 퍼징 도구. `FUZZ` 자리에 워드리스트를 끼워 요청한다.
  → [5장](part1/05-ffuf-wordlist.md)

매처 / 필터 (matcher / filter)
: ffuf 의 판정 방향. 매처(`-mc` 등)는 조건에 맞는 것만 남기고, 필터
  (`-fc` 등)는 맞는 것을 버린다. → [5장](part1/05-ffuf-wordlist.md)

soft-404
: 존재하지 않는 경로인데도 200 을 돌려주는 서버 동작. 상태코드만 보는
  오라클을 무력화하는 함정. → [6장](part1/06-response-oracle.md)

차분 필터 (size/word/time diff)
: 응답의 크기·단어수·시간이 기준선과 다른 것을 신호로 읽는 오라클.
  코드·크기가 같을 때 시간까지 내려간다. → [6장](part1/06-response-oracle.md)

타이밍 오라클 (timing oracle)
: 응답 내용이 동일해도 응답 시간의 차이로 존재를 판정하는 오라클. 잡음에
  취약해 반복 표본이 필요하다. → [6장](part1/06-response-oracle.md)

레이트리밋 (rate limit)
: 서버가 일정 시간당 요청 수를 제한하는 것. 초과 시 429 를 반환. 무례한
  퍼징은 히트가 429 에 묻혀 결과가 망가진다. → [7장](part1/07-stateful-and-reality.md)

범위 (scope)
: 감사에서 퍼징이 허용된 대상·시간·요청률의 계약된 경계. 범위 밖 퍼징은
  범죄가 될 수 있다. → [7장](part1/07-stateful-and-reality.md), [범위와 안전](scope-and-safety.md)

## API

OpenAPI (Swagger)
: API 의 경로·메서드·파라미터·응답 형태를 기술하는 스키마 표준. 퍼징의
  생성기이자 오라클이 된다. → [8장](part2/08-schema-as-grammar.md)

스키마 (schema)
: 유효한 요청·응답의 구조를 선언한 것. "문법"으로서 입력을 생성하고,
  뒤집으면 계약 검사(오라클)가 된다. → [8장](part2/08-schema-as-grammar.md)

Schemathesis
: OpenAPI 스키마로부터 테스트를 자동 생성해 계약 위반을 찾는 속성 기반
  API 테스팅 도구. → [9장](part2/09-schemathesis.md)

API 링크 (links)
: 한 응답의 값을 다음 요청의 입력으로 잇는 OpenAPI 의 선언. 상태저장
  시퀀스 퍼징의 생성기. → [10장](part2/10-stateful-sequences.md)

상태저장 시퀀스 (stateful sequence)
: register → login → token → me 처럼 앞 응답이 뒤 요청을 결정하는 요청
  나열. 호출 순서 자체가 입력이다. → [10장](part2/10-stateful-sequences.md)

BOLA (Broken Object Level Authorization)
: 한 사용자의 자격으로 다른 사용자의 자원에 접근·변경할 수 있는 인가
  결함. OWASP API Security Top 10 의 1위. 형태 오라클로는 못 잡는다.
  → [11장](part2/11-api-oracle.md)

5xx
: 서버 측 오류 상태코드. 클라이언트 입력이 무엇이든 발생하면 안 되므로
  스키마와 무관하게 항상 버그. → [11장](part2/11-api-oracle.md)

## web3

스마트컨트랙트 (smart contract)
: 블록체인 위에서 실행되는 프로그램. 상태가 영구히 누적되고 호출 순서가
  버그의 원천이 된다. → [12장](part3/12-contract-input-space.md)

Foundry (forge / anvil / cast)
: Solidity 스마트컨트랙트 개발·테스트 도구 모음. `forge` 가 퍼징·invariant
  테스트를 수행한다. → [13장](part3/13-forge-fuzz.md)

stateless fuzz
: 깨끗한 상태에서 함수를 한둘만 부르고 끝나는 퍼징. 상태·순서에 숨은
  버그를 놓친다. → [13장](part3/13-forge-fuzz.md)

invariant 테스트
: 함수들을 무작위 순서·인자로 엮으며 상태를 누적하고, 매번 불변식이
  유지되는지 검사하는 stateful 퍼징. → [14장](part3/14-invariant-handlers.md)

핸들러 (handler)
: invariant 퍼징에서 퍼저와 대상 컨트랙트 사이에 두는 컨트랙트. 유효한
  호출자와 의미 있는 인자를 제공해 깊은 상태에 도달시킨다. 없으면 대부분
  revert 로 낭비된다. → [14장](part3/14-invariant-handlers.md)

revert
: 스마트컨트랙트 실행이 조건(`require`)을 못 맞춰 되돌려지는 것. revert
  비율이 높으면 퍼저가 유효한 상태에 못 가고 있다는 신호. → [14장](part3/14-invariant-handlers.md)

shrink (반례 최소화)
: 불변식을 깬 호출 시퀀스를, 여전히 깨는 최소한의 호출로 줄여 보여주는
  것. 버그를 이해하기 쉽게 만든다. → [14장](part3/14-invariant-handlers.md)

self-transfer 인플레이션
: 자기 자신에게 토큰/지분을 보낼 때 잔액이 부풀려지는 버그. 오래된 값을
  캐시해 덮어쓸 때 발생. 이 교재 web3 랩의 심어둔 취약점. → [15장](part3/15-invariant-design.md)

ghost 변수 (ghost variable)
: 컨트랙트 자체엔 없지만 불변식 검사를 위해 핸들러/테스트가 따로 추적하는
  값 (예: 모든 참가자 지분의 합). → [14장](part3/14-invariant-handlers.md)

## 계측·일반

커버리지 가이드 퍼징 (coverage-guided fuzzing)
: 실행된 코드 커버리지를 피드백으로 삼아, 새 경로를 연 입력을 보존하며
  탐색을 편향시키는 방식. AFL++·libFuzzer 가 대표. → [2장](part0/02-five-elements.md)

계측 (instrumentation)
: 프로그램이 어느 코드를 실행했는지 기록하도록 심는 장치. 이 교재 장난감
  퍼저는 `sys.settrace`, 실무 도구는 컴파일 시점에 심는다. → [2장](part0/02-five-elements.md)

경계값 (boundary value)
: 0, -1, 최대값처럼 버그가 자주 숨는 극단 입력. 좋은 생성기가 우선 시험한다.
  → [13장](part3/13-forge-fuzz.md)
