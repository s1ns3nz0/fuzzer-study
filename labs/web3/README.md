# Part 3 랩 — web3 타겟 (Foundry)

12~15장이 쓰는 취약 볼트. invariant 퍼징을 가르치기 위해 직접 만든
최소 예제입니다. 모든 실습은 **로컬 EVM** 에서만 돕니다.

!!! `src/Vault.sol` 은 self-transfer 인플레이션 버그가 심어진 취약 컨트랙트입니다.

## 준비

```bash
# Foundry (한 번만)
curl -L https://foundry.paradigm.xyz | bash && foundryup

cd labs/web3
forge install foundry-rs/forge-std   # lib/ 는 gitignore 되어 있으니 한 번 설치
forge build
```

## 실행

```bash
forge test --match-contract VaultFuzzTest        # 13장: stateless fuzz (통과)
forge test --match-contract NaiveInvariantTest   # 14장: 핸들러 없는 invariant (버그 놓침)
forge test --match-contract VaultInvariantTest   # 14장: 핸들러 있는 invariant (버그 잡음)
```

## 파일

| 파일 | 무엇 | 장 |
|------|------|-----|
| `src/Vault.sol` | 취약 볼트 (self-transfer 인플레) | 12·15 |
| `test/VaultFuzz.t.sol` | stateless fuzz 속성 | 13 |
| `test/NaiveInvariant.t.sol` | 핸들러 없는 순진한 invariant | 14 |
| `test/VaultInvariant.t.sol` | 핸들러 + invariant | 14 |

## 요점

- 컨트랙트 입력공간은 함수 × 인자 × **호출 순서 × 누적 상태**(12장).
- stateless fuzz 는 상태·순서에 숨은 버그를 놓친다(13장).
- 핸들러가 유효 호출자·의미 있는 인자를 줘야 깊은 상태에 도달한다(14장).
- 무엇을 불변식으로 삼느냐가 성패를 가른다(15장).

실전 챌린지: [damn-vulnerable-defi](https://www.damnvulnerabledefi.xyz/).
