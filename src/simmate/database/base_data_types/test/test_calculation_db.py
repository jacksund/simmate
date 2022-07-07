# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import TestCalculation


@pytest.mark.django_db
def test_calculation_table():

    # test writing columns
    TestCalculation.show_columns()

    # test writing to database
    calc_db = TestCalculation.from_prefect_id(prefect_flow_run_id="example-id-123")
    calc_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    calc_db2 = TestCalculation.from_prefect_id(prefect_flow_run_id="example-id-123")
    assert calc_db.id == calc_db2.id

    # grab prefect url for this id
    assert (
        calc_db.prefect_cloud_link
        == "https://cloud.prefect.io/simmate/flow-run/example-id-123"
    )


@pytest.mark.django_db
def test_calculation_archives():

    calc_db = TestCalculation.from_prefect_id(prefect_flow_run_id="example-id-123")
    calc_db.save()
    calc_db2 = TestCalculation.from_prefect_id(prefect_flow_run_id="example-id-321")
    calc_db2.save()

    TestCalculation.objects.to_archive()

    TestCalculation.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )
