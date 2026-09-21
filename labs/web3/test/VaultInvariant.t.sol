// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, StdInvariant} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

/// 핸들러 — 퍼저가 호출할 함수 표면을 정의한다.
/// 정해진 actor 집합 안에서만 움직여, transfer 의 to 가 자기 자신이 될 수 있게 한다.
contract Handler is Test {
    Vault public vault;
    address[] public actors;
    address internal current;

    constructor(Vault _vault) {
        vault = _vault;
        actors = [address(0xA11CE), address(0xB0B), address(0xCAFE)];
        for (uint256 i = 0; i < actors.length; i++) {
            vm.deal(actors[i], 100 ether);
        }
    }

    modifier useActor(uint256 seed) {
        current = actors[seed % actors.length];
        vm.startPrank(current);
        _;
        vm.stopPrank();
    }

    function deposit(uint256 seed, uint256 amount) external useActor(seed) {
        amount = bound(amount, 0, current.balance);
        vault.deposit{value: amount}();
    }

    function withdraw(uint256 seed, uint256 amount) external useActor(seed) {
        amount = bound(amount, 0, vault.shares(current));
        vault.withdraw(amount);
    }

    function transfer(uint256 seed, uint256 toSeed, uint256 amount) external useActor(seed) {
        address to = actors[toSeed % actors.length]; // to 가 current 자신일 수 있다
        amount = bound(amount, 0, vault.shares(current));
        vault.transfer(to, amount);
    }

    function ghost_sumShares() external view returns (uint256 sum) {
        for (uint256 i = 0; i < actors.length; i++) {
            sum += vault.shares(actors[i]);
        }
    }
}

/// 14장 — invariant + handler. 무작위 호출 시퀀스 뒤에도 불변식이 유지되는지 본다.
contract VaultInvariantTest is StdInvariant, Test {
    Vault vault;
    Handler handler;

    function setUp() public {
        vault = new Vault();
        handler = new Handler(vault);
        targetContract(address(handler));
    }

    /// 불변식: 모든 지분의 합은 totalShares 와 같아야 한다.
    function invariant_sharesSumEqualsTotal() public view {
        assertEq(handler.ghost_sumShares(), vault.totalShares());
    }
}
