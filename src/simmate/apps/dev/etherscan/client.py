# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime

import pandas
import requests
from rich.progress import track

from simmate.configuration import settings


class EtherscanClient:
    """
    A minimal client to the Etherscan REST API.

    Most of code is forked from aioetherscan. If this app grows in scope,
    consider making it a dependency for the client + using objects.
     - https://github.com/ape364/aioetherscan/blob/master/aioetherscan/modules/account.py

    Accounts API Docs:
     - https://docs.etherscan.io/api-endpoints/accounts
    """

    api_url = "https://api.etherscan.io/v2/api"  # v2 endpoint
    api_key = settings.etherscan.api_key

    address_map = settings.etherscan.addresses

    chain_map = {
        "Ethereum": 1,
        "Base": 8453,
    }

    token_map = {
        "Ethereum": {
            # Stablecoins (1 token = $1)
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # Circle
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # Tether
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAO
            "USDS": "0xdC035D45d973E3EC169d2276DDab16f1e407384F",  # Sky
            # Wrapped Assets
            # "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # Wrapped Bitcoin
            # "rETH": "0xae78736Cd615f374D3085123A210448E74Fc6393",  # Rocket Pool ETH
            # Governance / Ownership
            # "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # Uniswap
            # "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",  # Compound
            # "POOL": "0x0cEC1A9154Ff802e7934Fc916Ed7Ca50bDE6844e",  # PoolTogether
        },
        "Base": {
            "USDC": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
            "USDS": "0x820c137fa70c8691f0e44dc420a5e53c168921dc",
            # "WBTC": "0x0555e30da8f98308edb960aa94c0db47230d2b9c",
            # "COMP": "0x9e1028f5f1d5ede59748ffcee5532509976840e0",
            # "rETH": "0xb6fe221fe9eef5aba221c348ba20a1bf5e73624c",
            # "POOL": "0xd652c5425aea2afd5fb142e120fecf79e18fafc3",
        },
    }

    token_precision_map = {
        "ETH": 1e18,
        "USDC": 1e6,
        "USDT": 1e6,
        "DAI": 1e18,
        "USDS": 1e18,
        "WBTC": 1e8,
        "rETH": 1e18,
        "UNI": 1e18,
        "COMP": 1e18,
        "POOL": 1e18,
    }

    transaction_type_map = {
        # Normal transaction = A transaction that is directly sent from one
        # externally-owned account (wallet) to another (or to a contract). It
        # has a from, to, value, and shows up as an on-chain tx with a hash.
        # Example: sending 1 ETH from your wallet to a friend.
        "normal": "txlist",
        # Internal transaction = Not a top-level tx, but an ETH transfer
        # triggered inside a smart contract as part of executing a normal tx.
        # They don’t have their own tx hash, only appear when you inspect the
        # trace. Example: you send ETH to a DeFi contract (normal tx), and that
        # contract forwards ETH to another address (internal tx).
        "internal": "txlistinternal",
        # ERC-20 = Fungible tokens (all units identical). Transfers represent
        # moving a quantity of tokens (e.g., USDC, DAI). Similar to moving
        # dollars (or stock) in a bank account.
        "token": "tokentx",  # ERC-20, Fungible tokens
        # ERC-721 = Non-fungible tokens (NFTs, each unique). Transfers represent
        # moving ownership of a specific tokenId (e.g., CryptoPunk #1234).
        "NFT": "tokennfttx",  # ERC-721
        # ERC-1155 = Multi-token standard (mix of fungible + non-fungible).
        # Transfers can move multiple tokenIds and amounts in a single
        # transaction (e.g., game items, where one ID is a unique sword and
        # another ID is stackable gold coins).
        "1155": "token1155tx",  # ERC-1155, Multi Token Standard
    }

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_transaction_data(cls) -> pandas.DataFrame:
        all_data = []
        for ens_name, address in cls.address_map.items():
            logging.info(f"Loading transactions for '{ens_name}'")
            data = cls.get_all_transactions(address=address)
            data["ens_name"] = ens_name
            all_data.append(data)
        return pandas.concat(all_data)

    @classmethod
    def get_all_balance_data(cls) -> pandas.DataFrame:
        all_data = []
        for ens_name, address in cls.address_map.items():
            logging.info(f"Loading balances for '{ens_name}'")
            balances = cls.get_all_balances(address=address)
            # flatten balances dict into a single dict
            balances_flat = {}
            for chain, tokens in balances.items():
                for token, amount in tokens.items():
                    if chain != "Ethereum":
                        key = f"{token}_{chain}"
                    else:
                        key = token
                    balances_flat[key] = amount
            balances_flat["address"] = address
            balances_flat["ens_name"] = ens_name
            all_data.append(balances_flat)
        return pandas.DataFrame(all_data)

    # -------------------------------------------------------------------------

    @classmethod
    def get_response(
        cls,
        action: str,
        address: str,
        module: str = "account",
        chain: str = "Ethereum",
        **kwargs,
    ):

        params = {
            "chainid": cls.chain_map[chain],
            "module": module,
            "action": action,
            "address": address,
            "apikey": cls.api_key,
            **kwargs,
        }
        response = requests.get(cls.api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "0" and data.get("message") == "No transactions found":
            data["result"] = None
        elif data.get("status") != "1":
            raise Exception(f"Etherscan Error: {data}")
        time.sleep(0.5)  # to avoid ratelimit of 5 requests per second
        return data

    def get_address_from_ens(ens_name: str) -> str:
        # !!! temp solution. Need lookup API when available
        return settings.etherscan.addresses[ens_name]

    def get_ens_from_address(address: str) -> str:
        # !!! temp solution. Need lookup API when available
        for ens_name, ens_addr in settings.etherscan.addresses.items():
            if ens_addr == address:
                return ens_name

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_balances(cls, address: str) -> dict:
        balances = {}
        for chain, tokens in cls.token_map.items():
            logging.info(f"Loading from '{chain}' chain")
            chain_balances = {}
            for token in track(tokens):
                chain_balances[token] = cls.get_token_balance(
                    chain=chain,
                    address=address,
                    token=token,
                )
            chain_balances["ETH"] = cls.get_balance(
                chain=chain,
                address=address,
            )
            balances[chain] = chain_balances
        return balances

    @classmethod
    def get_balance(cls, address: str, tag: str = "latest", **kwargs) -> float:
        response = cls.get_response(
            action="balance",
            address=address,
            tag=tag,
            **kwargs,
        )
        # result is in wei
        balance_wei = int(response["result"])
        balance_eth = balance_wei / cls.token_precision_map["ETH"]
        return balance_eth

    @classmethod
    def get_token_balance(
        cls,
        address: str,
        token: str,
        tag: str = "latest",
        chain: str = "Ethereum",
        **kwargs,
    ) -> float:
        response = cls.get_response(
            action="tokenbalance",
            contractaddress=cls.token_map[chain][token],
            address=address,
            tag=tag,
            chain=chain,
            **kwargs,
        )
        balance_token = int(response["result"]) / cls.token_precision_map[token]
        return balance_token

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_transactions(cls, address: str):
        all_data = []
        for chain in cls.chain_map:
            logging.info(f"Loading from '{chain}' chain")
            for transaction_type in track(cls.transaction_type_map):
                data = cls.get_transactions(
                    chain=chain,
                    address=address,
                    transaction_type=transaction_type,
                )
                data["transaction_type"] = transaction_type
                data["chain"] = chain
                all_data.append(data)
        return pandas.concat(all_data)

    @classmethod
    def get_transactions(
        cls,
        address: str,
        transaction_type: str = "normal",
        startblock: int = 0,
        endblock: int | str = "latest",
        **kwargs,
    ):

        # BUG: need to iterate to grab all pages
        page = 1
        offset = 100

        response = cls.get_response(
            address=address,
            action=cls.transaction_type_map[transaction_type],
            startblock=startblock,
            endblock=endblock,
            page=page,
            offset=offset,
            **kwargs,
        )
        data = pandas.DataFrame(response["result"])
        if data.empty:
            return data  # empty df

        # table is given entirely as str types, so we need to parse them
        column_type_map = {
            "blockNumber": int,
            "nonce": int,
            "transactionIndex": int,
            # these are technically ints (gwei) but we use float to avoid overflow
            "value": float,
            "gas": float,
            "gasPrice": float,
            "gasUsed": float,
            "cumulativeGasUsed": float,
            "txreceipt_status": int,
            "confirmations": int,
            "isError": int,
            # These can stay as str
            # 'type': str,
            # 'input': str,
            # 'methodId': str,
            # 'functionName': str,
            # 'contractAddress': str,
            # 'traceId': str,
            # 'errCode': str,
            # 'from': str,
            # 'to': str,
            # 'blockHash': str,
            # 'timeStamp': str, # datetime.timestamp, # handled below
            # 'hash': str,
        }
        for column in data.columns:
            dtype = column_type_map.get(column)
            if dtype:
                data[column] = data[column].astype(dtype)

        data["timeStamp"] = data["timeStamp"].apply(int).apply(datetime.fromtimestamp)

        data.replace({"": None}, inplace=True)

        # standardize symbol and amount
        token_verified_list = []
        amount_normalized_list = []
        for row in data.itertuples():

            # find verified token using contract address
            if row.contractAddress == None:
                # special case of Ethereum not having a contract address
                token_symbol = "ETH"
            else:
                # now rest of tokens
                verified_token_found = False
                for chain, tokens in cls.token_map.items():
                    for token_symbol, token_address in tokens.items():
                        if token_address == row.contractAddress:
                            verified_token_found = True
                            break
                    if verified_token_found:
                        break
                if not verified_token_found:
                    token_verified_list.append(None)
                    amount_normalized_list.append(None)
                    continue  # it is an unsupported token, maybe even scam one
            token_verified_list.append(token_symbol)

            # convert to proper units
            amount_normalized = (
                int(row.value) / cls.token_precision_map[token_symbol.split("_")[0]]
            )
            amount_normalized_list.append(amount_normalized)

        data["token_verified"] = token_verified_list
        data["amount_normalized"] = amount_normalized_list

        return data

    # -------------------------------------------------------------------------
