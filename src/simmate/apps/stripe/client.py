# -*- coding: utf-8 -*-

import stripe

from simmate.configuration import settings

# See https://dashboard.stripe.com/
stripe.api_key = settings.stripe.api_key


def get_checkout_url():
    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Fund Simmate USD Balance"},
                    "unit_amount": 1_00,  # in cents
                },
                "quantity": 1,
            }
        ],
        customer_email="john.doe@example.com",
        metadata={
            "first_name": "John",
            "last_name": "Doe",
            "user_id": "12345",
        },
        # automatic_tax={"enabled": True},  # requires user billing address
        success_url="https://simmate.org/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://simmate.org/cancel",
    )
    # checkout_session.status
    # checkout_session.payment_status
    return checkout_session.url


def get_transactions():
    from datetime import datetime, timedelta

    date = datetime.now() - timedelta(minutes=1)  # random timestamp for testing
    balance_transactions = stripe.BalanceTransaction.list(
        created={"gte": date}, limit=3
    )
    return balance_transactions
