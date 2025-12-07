# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class EthereumWallet(DatabaseTable):

    class Meta:
        db_table = "ethereum__wallets"

    # disable cols
    source = None

    html_display_name = "Ethereum Wallets"
    html_description_short = "Ethereum addresses monitored via Etherscan.io and Alchemy"

    external_website = "https://etherscan.io/"  # even if we pull from alchemy

    # -------------------------------------------------------------------------

    id = table_column.CharField(max_length=50, primary_key=True)
    """
    the Ethereum wallet address
    ex: 0x4F72261e6633738d591251a740eD421d2Ea4422E
    """

    ens_name = table_column.CharField(max_length=50, blank=True, null=True)

    assets = table_column.JSONField(blank=True, null=True)

    # -------------------------------------------------------------------------

    ethereum_balance = table_column.FloatField(blank=True, null=True)

    usdc_balance = table_column.FloatField(blank=True, null=True)

    stablecoin_options = [
        "USDC",
        "USDS",
    ]
    stablecoin_total_balance = table_column.FloatField(blank=True, null=True)

    assets_total_value_usd = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data_from_alchemy(cls):

        from ..client.alchemy import AlchemyClient

        wallet_balances = AlchemyClient.get_all_balance_data()

        # transactions = EtherscanClient.get_all_transaction_data()

    @classmethod
    def _load_data_from_etherscan(cls):

        from ..client.etherscan import EtherscanClient

        wallet_balances = EtherscanClient.get_all_balance_data()

        for wallet in wallet_balances.to_dict(orient="records"):
            wallet_cleaned = {
                k: v
                for k, v in wallet.items()
                if v != 0 and k not in ["address", "ens_name"]
            }
            ethereum_total = sum(
                [
                    v
                    for k, v in wallet_cleaned.items()
                    if k == "ETH" or k.startswith("ETH_")
                ]
            )
            stablecoin_total = sum(
                [
                    v
                    for k, v in wallet_cleaned.items()
                    if k in cls.stablecoin_options
                    or any([k.startswith(f"{sc}_") for sc in cls.stablecoin_options])
                ]
            )
            cls.objects.update_or_create(
                id=wallet["address"],
                defaults=dict(
                    ens_name=wallet["ens_name"],
                    tokens=wallet_cleaned,
                    ethereum_total=ethereum_total,
                    stablecoin_total=stablecoin_total,
                    # total_balance_usd -- need to calculate using price_catalog
                ),
            )

        # transactions = EtherscanClient.get_all_transaction_data()
