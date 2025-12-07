# -*- coding: utf-8 -*-

import logging

import pandas
import requests

from simmate.configuration import settings

from ..mappings import EthereumMappings


class AlchemyClient:

    api_key = settings.alchemy.api_key

    # used in building the base api endpoint like https://eth-mainnet.g.alchemy.com/v2/
    chain_map = {
        "Ethereum": "eth-mainnet",
        "Base": "base-mainnet",
    }

    transaction_type_map = {
        # Normal transaction = A transaction that is directly sent from one
        # externally-owned account (wallet) to another (or to a contract). It
        # has a from, to, value, and shows up as an on-chain tx with a hash.
        # Example: sending 1 ETH from your wallet to a friend.
        "normal": "external",
        # Internal transaction = Not a top-level tx, but an ETH transfer
        # triggered inside a smart contract as part of executing a normal tx.
        # They don’t have their own tx hash, only appear when you inspect the
        # trace. Example: you send ETH to a DeFi contract (normal tx), and that
        # contract forwards ETH to another address (internal tx).
        "internal": "internal",
        # ERC-20 = Fungible tokens (all units identical). Transfers represent
        # moving a quantity of tokens (e.g., USDC, DAI). Similar to moving
        # dollars (or stock) in a bank account.
        "token": "erc20",  # ERC-20, Fungible tokens
        # ERC-721 = Non-fungible tokens (NFTs, each unique). Transfers represent
        # moving ownership of a specific tokenId (e.g., CryptoPunk #1234).
        "NFT": "erc721",  # ERC-721
        # ERC-1155 = Multi-token standard (mix of fungible + non-fungible).
        # Transfers can move multiple tokenIds and amounts in a single
        # transaction (e.g., game items, where one ID is a unique sword and
        # another ID is stackable gold coins).
        "1155": "erc1155",  # ERC-1155, Multi Token Standard
    }
    # not inlcuded: 'token', 'specialnft'

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_transaction_data(cls) -> pandas.DataFrame:
        all_data = []
        for ens_name, address in EthereumMappings.wallet_addresses.items():
            logging.info(f"Loading transactions for '{ens_name}'")
            data = cls.get_all_transactions(address=address)
            data["ens_name"] = ens_name
            all_data.append(data)
        return pandas.concat(all_data)

    @classmethod
    def get_transactions_for_chain(cls, address: str, chain: str) -> pandas.DataFrame:
        # https://www.alchemy.com/docs/data/transfers-api/transfers-endpoints/alchemy-get-asset-transfers
        base_api_params = {
            # TODO: support incremental updates
            # fromBlock: hex(0),
            # toBlock: "latest",
            "category": [
                "external",  # ETH transfers
                "erc20",  # token transfers
            ],
            "contractAddresses": list(EthereumMappings.token_addresses[chain].values()),
            "order": "asc",
            "withMetadata": True,
            # "maxCount": hex(5),  # default (and max) is 1_000
        }

        # annoyingly, we can just pull all transaction in one call. We need to
        # do one call for "from" and a second for "to". Then combine them
        from_transactions = cls.get_response(
            method="alchemy_getAssetTransfers",
            params=[
                {
                    "fromAddress": address,
                    **base_api_params,
                }
            ],
            chain=chain,
        )
        to_transactions = cls.get_response(
            method="alchemy_getAssetTransfers",
            params=[
                {
                    "toAddress": address,
                    **base_api_params,
                }
            ],
        )

        # convert to pandas df and combine
        all_transactions = (
            from_transactions["result"]["transfers"]
            + to_transactions["result"]["transfers"]
        )
        return pandas.DataFrame(all_transactions)

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_balance_data(cls) -> pandas.DataFrame:
        all_data = []
        for ens_name, address in EthereumMappings.wallet_addresses.items():
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

    @classmethod
    def get_all_balances(cls, address: str) -> dict:
        balances = {}
        for chain in cls.chain_map.keys():
            logging.info(f"Loading from '{chain}' chain")
            chain_balances = cls.get_balances_for_chain(address, chain)[
                ["token_name", "token_amount"]
            ].to_dict(orient="records")
            balances[chain] = {
                e["token_name"]: e["token_amount"]
                for e in chain_balances
                if e["token_amount"] > 0
            }
        return balances

    @classmethod
    def get_balances_for_chain(cls, address: str, chain: str) -> dict:
        # https://www.alchemy.com/docs/data/token-api/token-api-endpoints/alchemy-get-token-balances
        api_params = [
            address,
            list(EthereumMappings.token_addresses[chain].values()),  # tokenSpec
        ]
        balances = cls.get_response(
            method="alchemy_getTokenBalances",
            params=api_params,
            chain=chain,
        )

        # Native token (ETH) must be done separately
        api_params = [
            address,
            "NATIVE_TOKEN",  # tokenSpec
        ]
        native_balance = cls.get_response(
            method="alchemy_getTokenBalances",
            params=api_params,
            chain=chain,
        )
        balances["result"]["tokenBalances"] += native_balance["result"]["tokenBalances"]

        df = pandas.DataFrame(balances["result"]["tokenBalances"])

        # convert hex strings to actual asset amounts
        token_names = []
        token_amounts = []
        for row in df.itertuples():
            if row.contractAddress != "null":
                token_name = [
                    name
                    for name, address in EthereumMappings.token_addresses[chain].items()
                    if address == row.contractAddress
                ][0]
            else:
                token_name = "ETH"
            precision = EthereumMappings.token_precisions[token_name]
            token_amount = int(row.tokenBalance, 16) / precision
            token_names.append(token_name)
            token_amounts.append(token_amount)
        df["token_name"] = token_names
        df["token_amount"] = token_amounts

        return df

    # -------------------------------------------------------------------------

    @classmethod
    def get_response(
        cls,
        method: str,
        params: list,
        chain: str = "Ethereum",
        recursive: bool = True,
    ):

        chain_name = cls.chain_map[chain]
        api_url = f"https://{chain_name}.g.alchemy.com/v2/{cls.api_key}"
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        assert "result" in data.keys()

        # TODO: catch errors that give 200 return code but error message response

        # perform a recursive call if the results are over multiple pages
        if recursive and "pageKey" in data["result"].keys():
            logging.info("API Results are paginated. Enumerating next.")

            full_results = cls.get_response(
                method=method,
                chain=chain,
                params=[
                    {
                        **params[0],
                        # current page key + original query is used to grab next page
                        "pageKey": data["result"]["pageKey"],  # must come last
                    }
                ],
            )
            # note: use "maxCount": hex(10) to practice pagination

            for concat_key in ["transfers"]:
                data["result"][concat_key] += full_results["result"][concat_key]
            data["result"].pop("pageKey")

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
