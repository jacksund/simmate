# -*- coding: utf-8 -*-

from django.utils.timezone import make_aware

from simmate.database.base_data_types import DatabaseTable, table_column

from ..client import EtherscanClient
from .wallets import EthereumWallet


class EthereumTransaction(DatabaseTable):

    class Meta:
        db_table = "ethereum__transactions"

    # disable cols
    source = None

    html_display_name = "Ethereum Transactions"
    html_description_short = "Ethereum transactions monitored via Etherscan.io"

    external_website = "https://etherscan.io/"

    # -------------------------------------------------------------------------

    id = table_column.CharField(max_length=50, primary_key=True)
    """
    the Ethereum transaction hash
    ex: 0x4F72261e6633738d591251a740eD421d2Ea4422E
    """

    created_at_original = table_column.DateTimeField(
        blank=True,
        null=True,
    )
    """
    Transaction timestamp
    """

    from_address = table_column.ForeignKey(
        to=EthereumWallet,
        related_name="transactions_recieved",
        on_delete=table_column.PROTECT,
    )

    to_address = table_column.ForeignKey(
        to=EthereumWallet,
        related_name="transactions_sent",
        on_delete=table_column.PROTECT,
    )

    asset_options = [
        "ETH",
        "USDC",
    ]
    asset = table_column.CharField(max_length=10, blank=True, null=True)

    amount = table_column.FloatField(blank=True, null=True)

    value_usd_original = table_column.FloatField(blank=True, null=True)
    # value at time of transaction

    value_usd = table_column.FloatField(blank=True, null=True)
    # value based on todays prices

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls):

        wallet_transactions = EtherscanClient.get_all_transaction_data()

        for transaction in wallet_transactions.to_dict(orient="records"):

            from_address = transaction["from"]
            to_address = transaction["to"]
            if not from_address or not to_address or not transaction["token_verified"]:
                continue

            # make sure the from/to wallets exist in the other table
            if not EthereumWallet.objects.filter(id=from_address).exists():
                EthereumWallet.objects.update_or_create(id=from_address)
            if not EthereumWallet.objects.filter(id=to_address).exists():
                EthereumWallet.objects.update_or_create(id=to_address)

            cls.objects.update_or_create(
                id=transaction["hash"],
                defaults=dict(
                    from_address_id=from_address,
                    to_address_id=to_address,
                    token=transaction["token_verified"],
                    amount=transaction["amount_normalized"],
                    created_at_original=(
                        make_aware(transaction["timeStamp"])
                        if transaction["timeStamp"]
                        else None
                    ),
                    # value_usd -- need to calculate using price_catalog
                    # value_usd_original
                ),
            )
