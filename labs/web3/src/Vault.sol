// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice 교육용 취약 볼트. ETH 를 1:1 지분(share)으로 예치/인출한다.
/// @dev transfer 에 self-transfer 인플레이션 버그가 심어져 있다.
///      실제 여러 ERC20 토큰에서 발견됐던 취약점 계보다.
contract Vault {
    mapping(address => uint256) public shares;
    uint256 public totalShares;

    /// ETH 를 예치하고 같은 양의 지분을 받는다.
    function deposit() external payable {
        shares[msg.sender] += msg.value;
        totalShares += msg.value;
    }

    /// 지분을 태우고 ETH 를 돌려받는다.
    function withdraw(uint256 amount) external {
        require(shares[msg.sender] >= amount, "insufficient");
        shares[msg.sender] -= amount;
        totalShares -= amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
    }

    /// 지분을 다른 주소로 옮긴다.
    /// @dev 버그: 잔액을 먼저 캐시한 뒤 각각 덮어쓴다. to == msg.sender 이면
    ///      두 번째 대입이 첫 번째를 덮어써서 지분이 amount 만큼 불어난다.
    function transfer(address to, uint256 amount) external {
        uint256 fromBal = shares[msg.sender];
        uint256 toBal = shares[to];
        require(fromBal >= amount, "insufficient");
        shares[msg.sender] = fromBal - amount;
        shares[to] = toBal + amount; // self-transfer 시 fromBal-amount 를 덮어씀 → 인플레이션
    }
}
