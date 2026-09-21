// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

/// 13장 — stateless fuzz. 함수 하나에 대한 속성(property)을 검사한다.
contract VaultFuzzTest is Test {
    Vault vault;

    function setUp() public {
        vault = new Vault();
    }

    /// 속성: 예치하면 그만큼 지분이 생긴다.
    function testFuzz_depositMintsShares(uint96 amount) public {
        vm.deal(address(this), amount);
        vault.deposit{value: amount}();
        assertEq(vault.shares(address(this)), amount);
        assertEq(vault.totalShares(), amount);
    }

    /// 속성: 예치 후 전액 인출하면 지분이 0 으로 돌아온다 (라운드트립).
    function testFuzz_depositWithdrawRoundtrip(uint96 amount) public {
        vm.deal(address(this), amount);
        vault.deposit{value: amount}();
        vault.withdraw(amount);
        assertEq(vault.shares(address(this)), 0);
    }

    receive() external payable {}
}
