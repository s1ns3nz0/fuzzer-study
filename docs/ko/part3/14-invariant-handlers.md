# 14. invariant 테스트와 핸들러 설계

**Part 3 · web3 감사**

13장의 stateless fuzz 는 볼트의 버그를 놓쳤습니다. 버그가 **상태와 호출
순서**에 숨어 있었기 때문입니다. 이 장은 그걸 잡는 도구 — invariant 퍼징 —
을 세우고, 그 성패를 가르는 **핸들러(handler)** 설계를 배웁니다.

이 장이 Part 0 의 커버리지 퍼저(2장)와 만나는 지점입니다. 거기선 피드백이
"새 코드를 연 입력을 코퍼스에 보존"이었습니다. 여기선 피드백이 "상태를
누적하며 함수들을 무작위 순서로 엮는 것"입니다. 형태는 달라도 같은 발상 —
**단발 입력이 아니라 시퀀스를 탐색한다.**

## 이 장에서 답할 질문

- invariant 테스트는 stateless fuzz 와 무엇이 다른가
- 왜 핸들러 없이는 invariant 가 대부분 헛돌며 버그를 놓치는가
- 핸들러는 무엇을 하고 어떻게 설계하는가

## 5요소 위치

이 장이 다루는 요소: **생성 + 피드백**

| 요소 | 이 장에서의 형태 |
|------|------------------|
| 생성 | 핸들러의 함수들을 무작위 순서로 호출 |
| 피드백 | **상태가 호출 사이에 누적된다 — 시퀀스가 곧 탐색 단위** |
| 오라클 | invariant 함수 (다음 장에서 정면으로) |

## 준비

```bash
cd labs/web3
forge build
```

## 1. invariant 테스트란

`forge` 의 invariant 테스트는 이렇게 돕니다.

1. `setUp` 으로 초기 상태를 만든다
2. **타겟 컨트랙트의 함수들을 무작위 순서·무작위 인자로 연달아 호출한다**
3. 매 호출 뒤(또는 시퀀스 끝) `invariant_*` 함수로 불변식을 검사한다
4. 불변식이 깨지면, 깨뜨린 **호출 시퀀스**를 최소화(shrink)해 보여준다

stateless fuzz 가 "함수 하나 × 여러 인자"였다면, invariant 는
"여러 함수 × 여러 순서 × 누적 상태"입니다. 12장에서 말한 컨트랙트의
진짜 입력공간을 정면으로 탐색합니다.

## 2. 순진한 시도 — 그리고 왜 실패하는가

가장 단순한 invariant 는 타겟 컨트랙트를 직접 퍼징하게 두는 것입니다.

```solidity
contract NaiveInvariantTest is StdInvariant, Test {
    function setUp() public {
        vault = new Vault();
        targetContract(address(vault));   // 볼트를 직접 두드려라
    }
    function invariant_totalNotInflated() public view {
        assertLe(vault.totalShares(), address(vault).balance);
    }
}
```

돌려봅니다.

```bash
forge test --match-contract NaiveInvariantTest
```

```text
| Contract | Selector | Calls | Reverts | Discards |
| Vault    | deposit  | 4210  | 0       | 0        |
| Vault    | transfer | 4315  | 4294    | 0        |
| Vault    | withdraw | 4275  | 4253    | 0        |
Suite result: ok. 1 passed; 0 failed
```

통과했습니다 — 하지만 버그를 못 잡은 겁니다. **Reverts 열을 보십시오.**
`transfer` 4315회 호출 중 **4294회가 revert**(99.5%), `withdraw` 도
4253/4275 revert 입니다.

이유는 13장과 같습니다. forge 가 `msg.sender` 를 무작위 주소로 잡는데,
그 주소는 지분이 0 입니다. 그래서 `transfer`·`withdraw` 의 `require(fromBal >=
amount)` 에서 거의 다 튕깁니다. **퍼저는 4천 번을 두드렸지만 대부분 문
앞에서 되돌아왔고, 볼트의 상태를 의미 있게 바꾼 호출은 극소수였습니다.**
버그가 있는 깊은 상태엔 도달조차 못 했습니다.

## 3. 핸들러 — 퍼저에게 유효한 손을 쥐여준다

해법은 **핸들러**입니다. 퍼저가 볼트를 직접 두드리게 하지 않고,
중간에 핸들러 컨트랙트를 둡니다. 핸들러는 두 가지를 합니다.

1. **유효한 호출자를 쓴다** — 미리 자금을 준 actor 집합 안에서만 `prank`
2. **인자를 의미 있게 제한한다** — `to` 를 무작위 주소가 아니라 actor 중에서 뽑고,
   `amount` 를 실제 잔고 범위로 `bound`

```solidity
contract Handler is Test {
    address[] public actors = [address(0xA11CE), address(0xB0B), address(0xCAFE)];

    modifier useActor(uint256 seed) {
        current = actors[seed % actors.length];   // 유효한 호출자
        vm.startPrank(current);
        _;
        vm.stopPrank();
    }

    function transfer(uint256 seed, uint256 toSeed, uint256 amount) external useActor(seed) {
        address to = actors[toSeed % actors.length];   // to 가 current 자신일 수 있다!
        amount = bound(amount, 0, vault.shares(current));   // 유효한 금액
        vault.transfer(to, amount);
    }
    // deposit, withdraw 도 같은 방식
}
```

두 설계 결정이 결정적입니다.

- **actor 집합이 작다** (3명). 그래서 `to` 가 호출자 자신과 같아지는 일이
  자주 일어납니다 — 13장에서 불가능했던 self-transfer 가 이제 가능합니다.
- **`bound` 로 유효 범위에 가둔다.** revert 로 낭비하지 않고, 매 호출이
  상태를 실제로 바꿉니다.

## 4. 핸들러를 타겟으로 invariant 실행

이제 볼트가 아니라 핸들러를 타겟으로 둡니다.

```solidity
contract VaultInvariantTest is StdInvariant, Test {
    function setUp() public {
        vault = new Vault();
        handler = new Handler(vault);
        targetContract(address(handler));    // 볼트가 아니라 핸들러를!
    }

    function invariant_sharesSumEqualsTotal() public view {
        assertEq(handler.ghost_sumShares(), vault.totalShares());
    }
}
```

불변식은 "모든 actor 지분의 합 = `totalShares`"입니다. 돌립니다.

```bash
forge test --match-contract VaultInvariantTest
```

```text
[FAIL: assertion failed: 1231912 != 659918]
	[Sequence] (original: 3, shrunk: 2)
	  deposit(seed=4747, amount=659918)
	  transfer(seed=..., toSeed=..., amount=571994)   ← to == 예치자 자신
 invariant_sharesSumEqualsTotal() (runs: 1, calls: 3, reverts: 0)
```

**잡았습니다.** 불변식이 깨졌습니다 — 지분 합 1231912 ≠ totalShares 659918.
그리고 forge 가 반례를 **2개 호출로 최소화**해 보여줍니다:

1. 누군가 659918 을 예치한다
2. 그 사람이 자기 자신에게 571994 를 transfer 한다 → 지분이 불어난다

self-transfer 인플레이션 버그입니다. `reverts: 0` 에 주목하세요 —
핸들러 덕에 두 호출 다 유효했고, 곧장 버그에 도달했습니다.
순진한 버전이 4천 번 헛돌던 것과 대조됩니다.

## 5. 핸들러 설계가 곧 탐색의 품질

이 장의 교훈은 하나입니다. **invariant 퍼징의 성패는 핸들러가 좌우합니다.**

| 핸들러 없이 | 핸들러 있게 |
|-------------|-------------|
| 무작위 호출자 → 99.5% revert | 유효 actor → revert 0 |
| `to` 가 주소 공간 전체 → self 불가능 | `to` 가 작은 집합 → self 가능 |
| 깊은 상태 도달 실패 | 2호출 만에 버그 |

핸들러는 "퍼저가 어디를 탐색할지"를 설계하는 일입니다. 너무 느슨하면
(순진한 버전) revert 로 낭비하고, 너무 빡빡하면 진짜 버그 경로를 막습니다.
**좋은 핸들러는 유효하되 충분히 넓은 손을 퍼저에게 쥐여줍니다.** 이건
실무 web3 감사에서 가장 손이 많이 가는, 그리고 가장 중요한 작업입니다.

그런데 아직 답 안 한 게 있습니다. 우리는 불변식으로 "지분 합 = totalShares"를
**골랐습니다.** 왜 하필 이것일까요? 다른 불변식이었다면 이 버그를 못 잡았을 수도
있습니다. 그게 다음 장 — 불변식 설계 — 의 주제입니다.

## 정리

- invariant 테스트: 함수들을 무작위 순서·인자로 엮으며 상태를 누적해 불변식을 검사한다.
- 핸들러 없이 타겟을 직접 두드리면 대부분 revert 로 낭비된다 (실측 99.5%).
- 핸들러는 유효 호출자와 의미 있는 인자(작은 actor 집합)를 줘서 깊은 상태에 도달시킨다.
- 결과: 순진한 버전이 못 잡은 버그를 2호출 최소 반례로 잡았다.

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Foundry 1.8.3, solc 0.8.37 |
| 랩 | `labs/web3` (`test/VaultInvariant.t.sol`, `test/NaiveInvariant.t.sol`) |
| 비고 | 반례의 구체적 값·호출 수는 씨앗에 따라 다릅니다. 재현되는 것은 "핸들러 없이는 통과(버그 놓침), 핸들러 있게는 self-transfer 반례로 실패"입니다. revert 비율도 실행마다 근소하게 다릅니다. |

## 참고

- Foundry invariant testing: <https://getfoundry.sh/forge/invariant-testing>
- 핸들러 패턴 심화: <https://getfoundry.sh/forge/invariant-testing#handler-based-testing>
- 불변식을 어떻게 고를 것인가 → [15장](15-invariant-design.md)
