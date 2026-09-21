// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import {Test, StdInvariant} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

// 순진한 invariant — Vault 를 직접 타겟. 핸들러 없음.
contract NaiveInvariantTest is StdInvariant, Test {
    Vault vault;
    function setUp() public {
        vault = new Vault();
        vm.deal(address(vault), 1000 ether);
        targetContract(address(vault));
    }
    function invariant_totalNotInflated() public view {
        // 핸들러가 없으니 sum 을 계산할 actor 집합도 없다.
        // 약한 대체 불변식: totalShares 는 예치 없이 늘 수 없다(예치 안 했으니 0 이어야).
        assertLe(vault.totalShares(), address(vault).balance);
    }
}
