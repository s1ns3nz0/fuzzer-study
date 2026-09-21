# 13. forge fuzz — 속성 기반 테스트 입문

**Part 3 · web3 감사**

12장에서 컨트랙트 입력공간의 지형을 봤습니다. 이 장은 Foundry 의 가장
기본적인 퍼징 — **stateless fuzz** 로 몸을 풉니다. 9장의 Schemathesis 와
같은 속성 기반 테스팅이고, Part 1·2 의 감각이 거의 그대로 옮겨옵니다.

## 이 장에서 답할 질문

- `forge` 의 fuzz 테스트는 어떻게 입력을 생성하는가
- 컨트랙트 함수의 "속성"을 어떻게 쓰는가
- stateless fuzz 가 못 보는 것은 무엇인가 (14장의 동기)

## 5요소 위치

이 장이 다루는 요소: **생성 + 오라클**

| 요소 | 이 장에서의 형태 |
|------|------------------|
| 생성 | 함수 인자를 타입에 맞춰 자동 생성 (`uint96 amount`) |
| 오라클 | 테스트 안의 `assert` — 속성이 곧 오라클 |
| 피드백 | 이 장은 없음 (단일 함수, 상태 누적 없음) → 14장 |

## 준비

```bash
cd labs/web3
forge build
```

## 1. fuzz 테스트의 문법

Foundry 에서 테스트 함수의 **인자에 타입을 주면**, 그 자리가 퍼징 대상이
됩니다. 인자 없는 함수는 일반 단위 테스트, 인자 있는 함수는 fuzz 테스트입니다.

```solidity
function testFuzz_depositMintsShares(uint96 amount) public {
    vm.deal(address(this), amount);       // 이 테스트에 amount 만큼 ETH 지급
    vault.deposit{value: amount}();
    assertEq(vault.shares(address(this)), amount);   // 속성(오라클)
    assertEq(vault.totalShares(), amount);
}
```

`amount` 를 사람이 정하지 않습니다. forge 가 `uint96` 범위에서 값을
자동 생성해 기본 256회 돌립니다. 0, 1, 최대값 같은 경계값을 우선 섞습니다 —
9장의 Hypothesis 와 같은 발상입니다.

!!! tip "왜 uint96 인가"
    `uint256` 전체를 쓰면 `vm.deal` 로 감당 못 할 천문학적 ETH 가 생성돼
    대부분 무의미하게 실패합니다. `uint96`(약 7.9×10²⁸ wei ≈ 79억 ETH)으로
    좁히면 현실적 범위에서 경계를 훑습니다. **생성 범위를 좁히는 것도 설계입니다.**

## 2. 속성이 곧 오라클

이 테스트의 오라클은 두 `assertEq` 입니다.

- "예치한 만큼 지분이 생겨야 한다"
- "totalShares 도 그만큼 늘어야 한다"

3장의 불변식 오라클과 같은 종류입니다 — 구체적 입출력이 아니라
**모든 입력에 참이어야 할 성질**을 씁니다. 라운드트립 속성도 하나 씁니다.

```solidity
function testFuzz_depositWithdrawRoundtrip(uint96 amount) public {
    vm.deal(address(this), amount);
    vault.deposit{value: amount}();
    vault.withdraw(amount);
    assertEq(vault.shares(address(this)), 0);   // 넣고 다 빼면 0 이어야
}
```

## 3. 실행

```bash
forge test --match-contract VaultFuzzTest
```

```text
Ran 2 tests for test/VaultFuzz.t.sol:VaultFuzzTest
[PASS] testFuzz_depositMintsShares(uint96) (runs: 256, μ: 90131, ~: 91221)
[PASS] testFuzz_depositWithdrawRoundtrip(uint96) (runs: 256, μ: 114183, ~: 115362)
Suite result: ok. 2 passed; 0 failed; 0 skipped
```

`runs: 256` — 각 테스트가 256개의 서로 다른 `amount` 로 실행됐고 전부
통과했습니다. `μ`(평균)·`~`(중앙값)는 가스 소모량입니다.

두 속성 다 통과입니다. 볼트의 예치·인출 라운드트립은 건전합니다.
**그런데 이 볼트에는 버그가 있습니다** (12장에서 예고했습니다).
왜 stateless fuzz 는 못 잡았을까요?

## 4. stateless fuzz의 맹점

이 테스트들은 각각 **깨끗한 상태에서 시작해, 함수를 한두 번 부르고, 끝냅니다.**
`setUp` 이 매번 새 볼트를 만드니 상태가 누적되지 않습니다.

하지만 볼트의 버그는 `transfer` 에 있고, **특정 호출 순서**로만 드러납니다
(자기 자신에게 보내는 self-transfer). stateless fuzz 로 이걸 잡으려면:

1. 지분이 있는 상태를 만들고 (deposit),
2. 그 상태에서 transfer 를 호출하되,
3. `to` 가 하필 `msg.sender` 자신이어야 합니다.

`transfer(address to, uint256 amount)` 를 stateless 로 퍼징하면 forge 는
`to` 를 `uint256` 주소 공간 전체에서 뽑습니다. 그게 하필 호출자 자신과
같을 확률은 사실상 0 입니다. 그래서 **버그를 영원히 못 만납니다.**

이게 12장에서 말한 컨트랙트의 본질입니다 — 버그가 상태와 순서에 숨습니다.
그걸 잡으려면 퍼저가 **상태를 누적하며 함수들을 무작위 순서로 엮어야** 합니다.
그리고 `to` 같은 인자를 아무 값이 아니라 **의미 있는 후보**(실제 참가자
주소)에서 뽑아야 합니다. 그게 다음 장의 invariant + handler 입니다.

## 정리

- forge fuzz: 테스트 함수 인자에 타입을 주면 그 자리가 자동 생성된다.
- 속성(assert)이 곧 오라클 — 9장 Schemathesis 와 같은 속성 기반 테스팅.
- 생성 범위(`uint96`)를 좁히는 것도 설계다.
- stateless fuzz 는 깨끗한 상태에서 함수 한둘만 부른다 → 상태·순서에 숨은 버그를 놓친다.

다음 장(14장)은 그 맹점을 메웁니다. 상태를 누적하며 함수들을 무작위로
엮는 **invariant 퍼징**, 그리고 인자를 의미 있게 뽑는 **핸들러**로,
이 볼트의 숨은 버그를 실제로 잡아냅니다.

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Foundry 1.8.3, solc 0.8.37 |
| 랩 | `labs/web3` (`test/VaultFuzz.t.sol`) |
| 비고 | 가스값(μ, ~)은 solc 버전·최적화 설정에 따라 다릅니다. |

## 참고

- Foundry fuzz testing: <https://getfoundry.sh/forge/fuzz-testing>
- 상태·순서에 숨은 버그를 잡으려면 → [14장](14-invariant-handlers.md)
