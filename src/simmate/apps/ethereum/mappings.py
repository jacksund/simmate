# -*- coding: utf-8 -*-

from simmate.configuration import settings


class EthereumMappings:

    wallet_addresses = settings.ethereum.addresses

    token_addresses = {
        "Ethereum": {
            # Stablecoins (1 token = $1)
            "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # Circle
            "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",  # Tether
            "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAO
            "USDS": "0xdc035d45d973e3ec169d2276ddab16f1e407384f",  # Sky
            # Wrapped Assets
            "wETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # Wrapped ETH
            "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # Wrapped Bitcoin
            "cbBTC": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",  # Coinbase Wrapped Bitcoin
            # Governance / Ownership
            "UNI": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # Uniswap
            "COMP": "0xc00e94cb662c3520282e6f5717214004a7f26888",  # Compound
            "POOL": "0x0cec1a9154ff802e7934fc916ed7ca50bde6844e",  # PoolTogether
            # Lending
            "AWETH": "0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8",  # Aave v3 WETH
            # Staking
            "rETH": "0xae78736cd615f374d3085123a210448e74fc6393",  # Rocket Pool ETH
            "stETH": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",  # Lido Staked ETH
            "wstETH": "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",  # Wrapped Lido Staked ETH
            # Savings
            "sUSDS": "0xa3931d71877c0e7a3148cb7eb4463524fec27fbd",  # Sky Savings
        },
        "Base": {
            # Stablecoins
            "USDC": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
            "USDS": "0x820c137fa70c8691f0e44dc420a5e53c168921dc",
            # Wrapped Assets
            "wETH": "0x4200000000000000000000000000000000000006",
            "WBTC": "0x0555e30da8f98308edb960aa94c0db47230d2b9c",
            "cbBTC": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
            # Governance / Ownership
            "COMP": "0x9e1028f5f1d5ede59748ffcee5532509976840e0",
            "POOL": "0xd652c5425aea2afd5fb142e120fecf79e18fafc3",
            "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",  # Aerodrome
            # Staking
            "rETH": "0xb6fe221fe9eef5aba221c348ba20a1bf5e73624c",
            # Savings
            "sUSDS": "0x5875eee11cf8398102fdad704c9e96607675467a",
        },
    }

    token_precisions = {
        "ETH": 1e18,
        # Stablecoins
        "USDC": 1e6,
        "USDT": 1e6,
        "DAI": 1e18,
        "USDS": 1e18,
        # Wrapped Assets
        "wETH": 1e18,
        "WBTC": 1e8,
        "cbBTC": 1e8,
        # Governance / Ownership
        "UNI": 1e18,
        "COMP": 1e18,
        "POOL": 1e18,
        "AERO": 1e18,
        # Lending
        "AWETH": 1e18,
        # Staking
        "rETH": 1e18,
        "stETH": 1e18,
        "wstETH": 1e18,
        # Savings
        "sUSDS": 1e18,
    }
