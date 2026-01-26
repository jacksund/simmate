# -*- coding: utf-8 -*-

import uuid

import pytest

from simmate.website.test_app.models import TestCalculation


@pytest.mark.django_db
def test_calculation_table():
    # test writing columns
    TestCalculation.show_columns()

    run_id = uuid.uuid4()

    # test writing to database
    calc_db = TestCalculation.from_run_context(
        run_id=run_id,
        workflow_name="example.test.workflow",
        workflow_version="1.2.3",
    )
    calc_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    calc_db2 = TestCalculation.from_run_context(
        run_id=run_id,
        workflow_name="example.test.workflow",
        workflow_version="1.2.3",
    )
    assert calc_db.id == calc_db2.id


@pytest.mark.django_db
def test_calculation_archives():
    calc_db = TestCalculation.from_run_context(
        run_id=uuid.uuid4(),
        workflow_name="example.test.workflow",
        workflow_version="1.2.3",
    )
    calc_db.save()
    calc_db2 = TestCalculation.from_run_context(
        run_id=uuid.uuid4(),
        workflow_name="example.test.workflow",
        workflow_version="1.2.3",
    )
    calc_db2.save()

    TestCalculation.objects.to_archive()

    TestCalculation.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )
