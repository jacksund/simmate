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

    html_display_name = "Wallets"
    html_description_short = (
        "Digital accounts that contain USDC or Token assets for budgeting and spending."
    )

    source = None  # disable col

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
        default=10_000,
    )

    # only for workers & validators
    collateral_balance = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls):

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

    def send(
        self,  # from_wallet
        to_wallet,
        usdc_amount: float = None,
        token_amount: float = None,
    ):
        # This send call does NOT create the equivalent transaction entry in
        # the Transaction table. You therefore do not call this method directly,
        # but instead use one of methods below that include creating a Transaction

        if usdc_amount:
            usdc_amount = Decimal(usdc_amount)
        if token_amount:
            token_amount = Decimal(token_amount)

        if self.id == to_wallet.id:
            raise Exception("to and from wallets can not be the same")

        if not usdc_amount and not token_amount:
            raise Exception("At least one amount (USDC or Token) must be given")

        if (usdc_amount and usdc_amount <= 0) or (token_amount and token_amount <= 0):
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
            if self.usdc_balance < usdc_amount:
                raise Exception("Insufficient USDC balance")
            to_wallet.token_balance += token_amount
            self.token_balance -= token_amount

        self.save()
        to_wallet.save()

    @classmethod
    def validate_ledger(cls):
        total_usdc = cls.objects.aggregate(
            total_usdc=Sum(F("usdc_balance") + F("collateral_balance"))
        )["total_usdc"]
        assert total_usdc == 0

        # TODO: check transaction history for individual wallets and make
        # sure each sums up to the wallet's current balances

    # -------------------------------------------------------------------------

    ### Transaction inputs ###
    # from_wallet
    # to_wallet,
    # usdc_amount: float = None,
    # token_amount: float = None,
    # collateral_amount: float = None,
    # status: str = None,
    # transaction_type: str = None,
    # transaction_subtype: str = None,
    # sending_user: str = None,
    # comments: str = None,

    @classmethod
    def send_promotion(
        cls,
        to_wallet,
        sending_user: User,
        usdc_amount: float,
        comments: str = None,
    ):

        from .transaction import Transaction

        from_wallet = cls.objects.get(wallet_type="simmate-treasury")

        assert sending_user.is_superuser

        with django_db_transaction.atomic():

            from_wallet.send(
                to_wallet=to_wallet,
                usdc_amount=usdc_amount,
            )

            transaction = Transaction(
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                usdc_amount=usdc_amount,
                status="Complete",  # no delay/review needed
                transaction_type="funding",
                transaction_subtype="Promotion",
                sending_user=sending_user,
                comments=comments,
            )
            transaction.save()

            cls.validate_ledger()

    def stake(
        self,  # from_wallet AND to_wallet
        amount: float,
        sending_user: User,
        comments: str,
    ):

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
                transaction_type="transfer",
                transaction_subtype=(
                    "Add Collateral" if amount > 0 else "Remove Collateral"
                ),
                sending_user=sending_user,
                comments=comments,
            )
            transaction.save()

            self.validate_ledger()
