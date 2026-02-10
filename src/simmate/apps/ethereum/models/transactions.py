# -*- coding: utf-8 -*-
from datetime import datetime

from django.utils.timezone import make_aware

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, table_column

from ..mappings import EthereumMappings
from .wallets import EthereumWallet


class EthereumTransaction(DatabaseTable):

    class Meta:
        db_table = "ethereum__transactions"

    # -------------------------------------------------------------------------

    html_display_name = "Ethereum Transactions"
    html_description_short = "Ethereum transactions monitored via Etherscan.io"

    external_website = "https://etherscan.io/"

    html_entries_template = "ethereum/transactions/table.html"
    html_entry_template = "ethereum/transactions/entry.html"

    # html_form_component = "ethereum-transaction-form"
    # html_enabled_forms = ["search"]

    # -------------------------------------------------------------------------

    id = table_column.CharField(max_length=75, primary_key=True)
    """
    the Ethereum transaction hash + unique label
    ex: 0x4F72261e6633738d591251a740eD421d2Ea4422E:log:123
    """

    hash = table_column.CharField(max_length=50, blank=True, null=True)
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

    chain_options = [
        "Ethereum",
        "Base",
    ]
    chain = table_column.CharField(max_length=25, blank=True, null=True)

    asset_options = list(EthereumMappings.token_precisions.keys())
    asset = table_column.CharField(max_length=10, blank=True, null=True)

    amount = table_column.DecimalField(
        max_digits=30,
        decimal_places=18,
        default=0,
    )

    value_usd_original = table_column.FloatField(blank=True, null=True)
    # value at time of transaction

    value_usd = table_column.FloatField(blank=True, null=True)
    # value based on todays prices

    # -------------------------------------------------------------------------

    @property
    def external_link(self) -> str:
        if self.chain == "Ethereum":
            return f"https://etherscan.io/tx/{self.hash}/"
        elif self.chain == "Base":
            return f"https://basescan.org/tx/{self.hash}/"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls):

        backend = settings.ethereum.backend

        if backend == "alchemy":
            cls._load_data_from_alchemy()

        elif backend == "etherscan":
            cls._load_data_from_etherscan()

        else:
            raise Exception(f"Unknown Ethereum backend: {backend}")

    @classmethod
    def _load_data_from_alchemy(cls):
        from ..clients.alchemy import AlchemyClient

        wallet_transactions = AlchemyClient.get_all_transaction_data()

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

            if transaction["metadata"]["blockTimestamp"]:
                date_str = transaction["metadata"]["blockTimestamp"]
                created_at_original = datetime.fromisoformat(date_str[:-1] + "+00:00")
            else:
                created_at_original = None

            cls.objects.update_or_create(
                id=transaction["uniqueId"],
                defaults=dict(
                    hash=transaction["hash"],  # those of the same swap with match
                    from_address_id=from_address,
                    to_address_id=to_address,
                    chain=transaction["chain"],
                    asset=transaction["token_verified"],
                    amount=transaction["amount_verified"],
                    created_at_original=created_at_original,
                    # value_usd -- need to calculate using price_catalog
                    # value_usd_original
                ),
            )

    @classmethod
    def _load_data_from_etherscan(cls):

        from ..clients.etherscan import EtherscanClient

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
