# -*- coding: utf-8 -*-

from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction as django_db_transaction
from django.db.models import F, Sum

from simmate.database.base_data_types import DatabaseTable, table_column

from .project import Project


class Wallet(DatabaseTable):

    class Meta:
        db_table = "project_management__wallets"

    # -------------------------------------------------------------------------

    html_display_name = "Wallets"
    html_description_short = (
        "Digital accounts that contain USDC or Token assets for budgeting and spending."
    )

    html_entries_template = "project_management/wallet/table.html"
    html_entry_template = "project_management/wallet/view.html"

    # -------------------------------------------------------------------------

    wallet_type_options = [
        "project",
        "user",
        # unique types where only one exists for each:
        "simmate-treasury",
        "simmate-escrow",
        "validator-pool",
        "simmate-bridge",  # record keeping for on/off ramps
    ]
    wallet_type = table_column.CharField(max_length=30, blank=True, null=True)
    """
    Whether the wallet is owned by a specific user or project.
    """

    user = table_column.OneToOneField(
        User,
        on_delete=table_column.PROTECT,
        related_name="wallet",
        blank=True,
        null=True,
    )

    project = table_column.OneToOneField(
        Project,
        on_delete=table_column.PROTECT,
        related_name="wallet",
        blank=True,
        null=True,
    )

    usdc_balance = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )

    token_balance = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )

    # only for workers & validators
    collateral_balance = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls):

        # ensure default wallets exist
        for wallet in [
            "simmate-treasury",
            "simmate-escrow",
            "validator-pool",
            "simmate-bridge",
        ]:
            cls.objects.get_or_create(wallet_type=wallet)
            if cls.objects.filter(wallet_type=wallet).count() != 1:
                raise Exception(f"More than one entry for wallet type {wallet}")

        # check ethereum blockchain for new USDC transactions
        # TO-DO

    # -------------------------------------------------------------------------

    @classmethod
    def validate_ledger(cls, usdc: bool = True, tokens: bool = True):

        if usdc:
            total_usdc = cls.objects.aggregate(
                total_usdc=Sum(F("usdc_balance") + F("collateral_balance"))
            )["total_usdc"]
            assert total_usdc == 0

        if tokens:
            total_tokens = cls.objects.aggregate(total_tokens=Sum("token_balance"))[
                "total_tokens"
            ]
            assert total_tokens == 0

        # TODO: check transaction history for individual wallets and make
        # sure each sums up to the wallet's current balances

    # -------------------------------------------------------------------------

    def send(
        self,  # from_wallet
        to_wallet,
        usdc_amount: float = 0,
        token_amount: float = 0,
        #
        status: str = None,
        transaction_type: str = None,
        transaction_subtype: str = None,
        sending_user: User = None,
        comments: str = None,
    ):

        from .transaction import Transaction

        with django_db_transaction.atomic():

            if usdc_amount:
                usdc_amount = Decimal(usdc_amount)
            if token_amount:
                token_amount = Decimal(token_amount)

            if self.id == to_wallet.id:
                raise Exception("to and from wallets can not be the same")

            if not usdc_amount and not token_amount:
                raise Exception("At least one amount (USDC or Token) must be given")

            if (usdc_amount and usdc_amount <= 0) or (
                token_amount and token_amount <= 0
            ):
                raise Exception("Amounts must be greater than 0")

            if usdc_amount:
                # only the treasury & bridge are allowed to have a negative USDC balance
                if (
                    self.wallet_type not in ["simmate-bridge", "simmate-treasury"]
                    and self.usdc_balance < usdc_amount
                ):
                    raise Exception("Insufficient USDC balance")
                to_wallet.usdc_balance += usdc_amount
                self.usdc_balance -= usdc_amount

            if token_amount:
                # only the bridge can have a negative token balance
                if (
                    self.wallet_type not in ["simmate-bridge"]
                    and self.token_balance < token_amount
                ):
                    raise Exception("Insufficient Token balance")

                # block unrealistic balances (>$1 billion)
                expected_amt = to_wallet.token_balance + token_amount
                if expected_amt > 1_000_000_000:
                    raise Exception("Unrealistic Token Balance (>$1 billion)")

                to_wallet.token_balance += token_amount
                self.token_balance -= token_amount

            self.save()
            to_wallet.save()

            transaction = Transaction(
                from_wallet=self,
                to_wallet=to_wallet,
                #
                usdc_amount=usdc_amount,
                token_amount=token_amount,
                #
                status=status,
                transaction_type=transaction_type,
                transaction_subtype=transaction_subtype,
                sending_user=sending_user,
                comments=comments,
            )
            transaction.save()

            self.validate_ledger()

    def stake(
        self,  # from_wallet AND to_wallet
        amount: float,
        sending_user: User,
        comments: str,
    ):
        # a unique internal transaction where funds are moved within the same wallet

        from .transaction import Transaction

        amount = Decimal(amount)

        if amount > 0 and self.usdc_balance < amount:
            raise Exception("Insufficient USDC balance")
        elif amount < 0 and self.collateral_balance < amount:
            raise Exception("Insufficient Collateral balance")
        else:
            raise Exception("Staking amount must be non-zero")

        with django_db_transaction.atomic():

            self.usdc_balance -= amount
            self.collateral_balance += amount
            self.save()

            transaction = Transaction(
                from_wallet=self,
                to_wallet=self,
                usdc_amount=amount,
                collateral_amount=amount * -1,
                status="Complete",  # no delay/review needed
                transaction_type="Transfer",
                transaction_subtype=(
                    "Add Collateral" if amount > 0 else "Remove Collateral"
                ),
                sending_user=sending_user,
                comments=comments,
            )
            transaction.save()

            self.validate_ledger()

    # -------------------------------------------------------------------------

    # utils to help with common transaction types + populating metadata

    def send_promotion(
        self,
        usdc_amount: float,
        sending_user: User,
        comments: str = None,
    ):

        from_wallet = self.__class__.objects.get(wallet_type="simmate-treasury")

        assert sending_user.is_superuser

        from_wallet.send(
            to_wallet=self,
            usdc_amount=usdc_amount,
            #
            status="Complete",  # no delay/review needed
            transaction_type="Fund",
            transaction_subtype="Promotion",
            sending_user=sending_user,
            comments=comments,
        )

    def adjust_tokens(
        self,
        token_amount: float,
        sending_user: User,
        comments: str = None,
    ):

        bridge_wallet = self.__class__.objects.get(wallet_type="simmate-bridge")

        if token_amount < 0:
            # flip the transaction so that it is a positive amount transfered
            from_wallet = self
            to_wallet = bridge_wallet
            token_amount = abs(token_amount)
            transaction_subtype = "Remove Tokens"
        else:
            from_wallet = bridge_wallet
            to_wallet = self
            transaction_subtype = "Add Tokens"

        from_wallet.send(
            to_wallet=to_wallet,
            token_amount=token_amount,
            #
            status="Complete",  # no delay/review needed
            transaction_type="Adjust",
            transaction_subtype=transaction_subtype,
            sending_user=sending_user,
            comments=comments,
        )

    # -------------------------------------------------------------------------
