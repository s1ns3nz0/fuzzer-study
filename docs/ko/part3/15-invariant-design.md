# 15. 불변식 설계와 취약 컨트랙트 깨기

**Part 3 · web3 감사**

14장은 도구를 세웠습니다 — invariant + 핸들러. 하지만 마지막 질문을
남겼습니다. **우리는 "지분 합 = totalShares"를 불변식으로 골랐다. 왜?**

이 장은 그 질문에 답합니다. 도구는 불변식을 깨는 입력을 찾아줍니다.
하지만 **무엇이 불변식인지는 사람이 정합니다.** 그리고 그 선택이 감사의
성패를 가릅니다 — 잘못된 불변식은 버그를 못 잡거나, 있지도 않은 버그를
신고합니다. 이게 web3 감사에서 가장 어렵고 가장 가치 있는 기술입니다.

## 이 장에서 답할 질문

- 좋은 불변식은 어디서 오는가
- 왜 어떤 불변식은 버그를 잡고 어떤 건 못 잡는가
- 우리 볼트의 버그는 정확히 무엇이고, 어떻게 고치는가

## 5요소 위치

이 장이 다루는 요소: **오라클** (불변식이 곧 오라클)

## 1. 버그의 정체

먼저 볼트의 버그를 정확히 해부합니다 (`labs/web3/src/Vault.sol`).

```solidity
function transfer(address to, uint256 amount) external {
    uint256 fromBal = shares[msg.sender];
    uint256 toBal = shares[to];
    require(fromBal >= amount, "insufficient");
    shares[msg.sender] = fromBal - amount;
    shares[to] = toBal + amount;       // ← 여기
}
```

`to == msg.sender` 인 경우를 손으로 따라가 봅니다. 지분이 100 인 사람이
자기 자신에게 30 을 보냅니다.

```
fromBal = shares[X] = 100      // 캐시
toBal   = shares[X] = 100      // 캐시 (같은 슬롯!)
shares[X] = fromBal - amount = 70    // 첫 대입
shares[X] = toBal   + amount = 130   // 둘째 대입이 첫째를 덮어씀
```

결과: `shares[X] = 130`. **30 이 무에서 생겼습니다.** `totalShares` 는
안 바뀌었으니, 이제 "지분 합 > totalShares" 입니다. 이 사람은 넣은 것보다
많이 인출할 수 있습니다 — 다른 사람의 예치금을 훔치는 셈입니다.

원인은 **오래된 값(stale read)의 덮어쓰기**입니다. `from` 과 `to` 를 각각
캐시했는데 둘이 같은 슬롯일 때, 두 번째 쓰기가 첫 번째를 무효화합니다.
실제 여러 ERC20 토큰에서 발견된 취약점 계보입니다.

## 2. 어떤 불변식이 이 버그를 잡는가

이제 핵심입니다. 여러 불변식 후보를 놓고, 각각이 이 버그를 잡는지 봅니다.

### 후보 A — `totalShares <= 컨트랙트 잔고`

14장의 순진한 버전이 쓴 것입니다. **이 버그를 못 잡습니다.**
self-transfer 는 `shares` 매핑만 부풀리고 `totalShares` 는 안 건드립니다.
그래서 `totalShares` 는 여전히 잔고와 일치합니다. 불변식이 엉뚱한 곳을
보고 있었습니다.

### 후보 B — `sum(모든 지분) == totalShares`

14장이 잡은 것입니다. **이 버그를 잡습니다.** self-transfer 가 지분 합을
30 늘렸지만 `totalShares` 는 그대로라, 등식이 깨집니다. 버그가 실제로
망가뜨리는 바로 그 관계를 봅니다.

### 두 후보의 차이

| 불변식 | 무엇을 보나 | self-transfer 버그 |
|--------|-------------|--------------------|
| A: `totalShares <= balance` | 회계 총량 vs 실물 | ❌ 못 잡음 |
| B: `sum(shares) == totalShares` | 분산 장부 vs 집계 | ✅ 잡음 |

교훈: **불변식은 버그가 실제로 위반하는 관계를 겨냥해야 한다.**
후보 A 도 참인 성질이지만(이 버그로는 안 깨짐), 이 버그를 못 봅니다.
좋은 불변식은 "무엇이 참이어야 하는가"뿐 아니라 "무엇이 깨질 수 있는가"를
함께 생각해야 나옵니다.

## 3. 좋은 불변식은 어디서 오는가

실무에서 불변식은 세 곳에서 옵니다.

**보존 법칙.** 무언가가 생기거나 사라지면 안 됩니다.
"지분 합 = 총량", "총공급량 불변", "들어온 ETH = 나갈 ETH + 잔고".
회계 시스템의 이중부기 원리입니다. 우리 버그를 잡은 후보 B 가 이겁니다.

**단조성·경계.** 어떤 값은 특정 방향으로만 움직이거나 범위를 벗어나면 안
됩니다. "담보 비율은 청산선 아래로 안 간다", "누구도 음수 잔고를 못 가진다".

**권한·접근.** "관리자만 mint 할 수 있다", "예치자만 자기 몫을 뺀다".
11장의 BOLA 가 이 부류의 web3 판입니다.

불변식을 찾는 실전 질문: **"이 컨트랙트가 돈을 잃는다면, 어떤 등식이
깨져 있을까?"** 그 등식을 쓰면 그게 불변식입니다.

## 4. 버그 고치고 재검증

버그를 고칩니다. 캐시를 쓰지 않고, 대입을 순차로 반영합니다.

```solidity
function transfer(address to, uint256 amount) external {
    require(shares[msg.sender] >= amount, "insufficient");
    shares[msg.sender] -= amount;    // 먼저 빼고
    shares[to] += amount;            // 그 결과 위에 더한다 (self 여도 안전)
}
```

이제 self-transfer 는 `shares[X] -= 30` 후 `shares[X] += 30` 이라 no-op 입니다.
`labs/web3/src/Vault.sol` 을 이렇게 고치고 invariant 를 다시 돌리면
후보 B 가 통과합니다 — 버그가 사라졌으니까요. (직접 고쳐 확인해 보십시오.)

!!! tip "고친 뒤에도 퍼징하라"
    버그를 고친 뒤 invariant 가 통과한다고 끝이 아닙니다. 불변식이
    통과하는 건 "이 불변식으로는 버그를 못 찾았다"는 뜻이지 "버그가 없다"가
    아닙니다(3장·1장의 한계). 그래서 불변식을 여러 개 겹쳐 씁니다 —
    보존, 경계, 권한을 각각.

## 5. 실전으로: damn-vulnerable-defi

이 랩은 self-transfer 하나에 집중한 최소 예제였습니다. 실전 감각을 원하면
[damn-vulnerable-defi](https://www.damnvulnerabledefi.xyz/) 를 권합니다 —
실제 DeFi 취약점 계보(가격 조작, 플래시론, 재진입 등)를 Foundry 로 푸는
챌린지 모음입니다. 각 챌린지에서 스스로 물어보십시오. **"여기서 깨질 수
있는 불변식은 무엇인가?"** 이 파트에서 배운 건 도구가 아니라 그 질문입니다.

## Part 3 정리

- web3 오라클은 거의 전부 불변식이고, 무엇이 불변식인지는 사람이 정한다.
- 같은 버그도 불변식을 잘못 고르면(후보 A) 못 잡고, 제대로 고르면(후보 B) 잡는다.
- 좋은 불변식은 보존 법칙·단조성·권한에서 온다 — "돈을 잃으면 어떤 등식이 깨지나?"
- 도구(forge)는 불변식을 깨는 입력을 찾을 뿐, 불변식 자체는 감사자의 통찰이다.

## 검증 로그

!!! note "실행 증거 의무"
    이 문서의 명령어와 출력은 아래 환경에서 실제로 실행해 얻은 것입니다.

| 항목 | 값 |
|------|-----|
| 검증 여부 | ✅ 검증됨 |
| 검증 일자 | 2026-09-21 |
| 도구 버전 | Foundry 1.8.3, solc 0.8.37 |
| 랩 | `labs/web3` (`src/Vault.sol`, invariant 후보 A/B 대비) |
| 비고 | 후보 A(못 잡음)/B(잡음) 대비는 `NaiveInvariant`(A)·`VaultInvariant`(B) 로 재현됩니다. |

## 참고

- damn-vulnerable-defi: <https://www.damnvulnerabledefi.xyz/>
- 불변식 설계 사례: Trail of Bits, "Building Secure Contracts" — Echidna/Foundry invariants
- 오라클 분류의 뿌리 → [3장](../part0/03-oracle-problem.md)
- 세 도메인 종합 비교 → [16장](../part4/16-comparison.md)
