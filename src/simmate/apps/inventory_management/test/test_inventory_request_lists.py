import re
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from simmate.apps.inventory_management.components import (
    InventoryRequestComponent,
    InventoryRequestListComponent,
)
from simmate.apps.inventory_management.datastores import SubstanceDatastore
from simmate.apps.inventory_management.models import (
    InventoryRequest,
    InventoryRequestList,
    Mixture,
    Molecule,
    Substance,
)
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.website.htmx.components import HtmxComponent


def make_ethanol() -> Substance:
    molecule = Molecule.from_toolkit(molecule=ToolkitMolecule.from_smiles("CCO"))
    molecule.save()
    return Substance.objects.create(id="BCD-012-0004", molecule=molecule)


# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_resolve_items(django_assert_max_num_queries):
    substance = Substance.objects.create(id="BCD-012-0001")
    Substance.objects.create(id="BCD-012-0002", is_delisted=True, replaced_by=substance)
    Substance.objects.create(id="BCD-012-0003", is_delisted=True)
    ethanol = make_ethanol()
    mixture = Mixture.objects.create(id_prefix="BCDF")
    open_request = InventoryRequest.objects.create(
        substance=substance, status="In Progress"
    )
    InventoryRequest.objects.create(substance=ethanol, status="Completed")

    items = [
        "BCD-012-0001",
        " bcd-012-0002 ",  # merged, typed in lowercase
        "BCD-012-0003",  # delisted
        "BCD-012-9999",  # not registered
        f"BCDF-{mixture.id}",
        f"GHJK-{mixture.id}",  # wrong prefix
        "OCC",  # same as ethanol
        "c1ccccc1",  # new
        "not a smiles",
        "",
    ]
    with django_assert_max_num_queries(6):
        infos = InventoryRequest.resolve_items(items)

    assert "" not in infos
    assert infos["BCD-012-0001"]["kind"] == "substance"
    assert infos["BCD-012-0001"]["open_request_ids"] == [open_request.display_id]

    merged = infos["bcd-012-0002"]
    assert merged["kind"] == "substance"
    assert merged["substance_id"] == substance.id
    assert merged["merged_from"] == "BCD-012-0002"
    assert merged["open_request_ids"] == [open_request.display_id]

    assert infos["BCD-012-0003"]["kind"] == "invalid"
    assert "delisted" in infos["BCD-012-0003"]["error"]
    assert infos["BCD-012-9999"]["kind"] == "invalid"

    assert infos[f"BCDF-{mixture.id}"]["kind"] == "mixture"
    assert infos[f"BCDF-{mixture.id}"]["mixture_id"] == mixture.id
    assert infos[f"GHJK-{mixture.id}"]["kind"] == "invalid"

    # SMILES give a preview of the matching substance, and closed requests
    # are not listed
    assert infos["OCC"]["kind"] == "smiles"
    assert infos["OCC"]["substance_id"] == ethanol.id
    assert infos["OCC"]["open_request_ids"] == []
    assert infos["c1ccccc1"]["kind"] == "smiles"
    assert infos["c1ccccc1"]["substance_id"] is None
    assert infos["not a smiles"]["kind"] == "invalid"


def test_parse_table():
    rows = InventoryRequestList.parse_table(
        ["Substance ID", "Amount", "Units", "Notes", "Unnamed: 4"],
        [
            ["BCD-012-0001", 50.0, "MG", None, ""],
            ["CCO", float("nan"), None, "for the assay", None],
            [None, "", None, None, None],  # blank records are dropped
            ["CCN"],  # short records are padded
        ],
    )
    assert rows == [
        dict(item="BCD-012-0001", amount="50", amount_units="mg", comments=""),
        dict(item="CCO", amount="", amount_units="", comments="for the assay"),
        dict(item="CCN", amount="", amount_units="", comments=""),
    ]

    with pytest.raises(ValueError, match="Unknown column"):
        InventoryRequestList.parse_table(["item", "color"], [])
    with pytest.raises(ValueError, match="'item' column is required"):
        InventoryRequestList.parse_table(["amount"], [])
    with pytest.raises(ValueError, match="More than one column"):
        InventoryRequestList.parse_table(["smiles", "substance_id"], [])
    with pytest.raises(ValueError, match="column without a header"):
        InventoryRequestList.parse_table(["item"], [["CCO", "extra"]])


@pytest.mark.django_db
def test_check_rows():
    substance = Substance.objects.create(id="BCD-012-0001")
    open_request = InventoryRequest.objects.create(
        substance=substance, status="Under Review"
    )
    rows = [
        dict(item="BCD-012-0001", amount="50"),  # units from shared values
        dict(item="CCO", amount="abc"),
        dict(item="CCO", amount_units="lbs", priority="URGENT"),
        dict(),  # blank rows are skipped
        dict(item="c1ccccc1", needed_by="next week", estimated_cost="-1"),
        dict(amount="5", amount_units="mg"),  # no item
        dict(item="CCN", amount="5", amount_units=""),
        dict(item="CCCC", color="blue"),
    ]
    shared = dict(priority="Medium", supplier="Sigma-Aldrich")
    checked_rows, errors, warnings = InventoryRequestList.check_rows(rows, shared)

    by_number = {row["number"]: row for row in checked_rows}
    assert by_number[1]["status"] == "substance"
    assert by_number[1]["errors"] == ["has an amount but no amount_units."]
    assert by_number[1]["warnings"] == [
        f"already has open request(s): {open_request.display_id}."
    ]
    assert by_number[2]["status"] == "new"
    assert "amount must be a number" in by_number[2]["errors"][0]
    assert by_number[3]["warnings"] == ["is the same item as row 2."]
    assert len(by_number[3]["errors"]) == 2  # units and priority
    assert by_number[4]["status"] == "blank"
    assert len(by_number[5]["errors"]) == 2  # date and cost
    assert by_number[6]["errors"] == ["has no item."]
    assert by_number[7]["errors"] == ["has an amount but no amount_units."]
    assert by_number[8]["errors"] == ["has unknown columns: color."]

    assert errors[0] == "Row 1: has an amount but no amount_units."
    assert len(warnings) == 2

    # shared values fill blank cells, but a row's own value is used first
    assert by_number[1]["values"]["priority"] == "Medium"
    assert by_number[1]["values"]["supplier"] == "Sigma-Aldrich"
    assert by_number[1]["values"]["amount"] == Decimal("50.000")

    # good rows have no messages
    checked_rows, errors, warnings = InventoryRequestList.check_rows(
        [dict(item="CCO", amount="2.5", amount_units="G", priority="high")],
        dict(priority="Low", needed_by="2026-12-01 00:00:00"),
    )
    assert not errors and not warnings
    values = checked_rows[0]["values"]
    assert values["amount_units"] == "g"
    assert values["priority"] == "High"
    assert values["needed_by"].isoformat() == "2026-12-01"

    # lists can't be empty or too long
    _, errors, _ = InventoryRequestList.check_rows([dict()])
    assert errors == ["Add at least one item to request."]
    too_many = [dict(item="CCO")] * (InventoryRequestList.max_requests + 1)
    _, errors, _ = InventoryRequestList.check_rows(too_many)
    assert "at most" in errors[-1]

    # shared users and projects must exist
    _, errors, _ = InventoryRequestList.check_rows(
        [dict(item="CCO")], dict(requested_by_id=123456)
    )
    assert errors == ["Shared requested_by_id must be the ID of a User."]


@pytest.mark.django_db
def test_create_with_requests(mocker, admin_user):
    substance = Substance.objects.create(id="BCD-012-0001")
    mixture = Mixture.objects.create(id_prefix="BCDF")
    spy = mocker.spy(SubstanceDatastore, "get_or_create_ids")

    request_list = InventoryRequestList.create_with_requests(
        title="Round 3 targets",
        rows=[
            dict(item="BCD-012-0001", amount="50", amount_units="mg"),
            dict(item=mixture.display_id, priority="High"),
            dict(item="CCO"),
            dict(item="CCN"),
            dict(),
        ],
        shared=dict(priority="Low", fulfillment_type="Internal Synthesis"),
        description="testing",
        submitted_by=admin_user,
    )

    # all new SMILES are registered together
    assert spy.call_count == 1
    assert len(spy.call_args.args[-1]) == 2

    assert request_list.display_id.startswith("RL-")
    assert request_list.submitted_by == admin_user
    requests = list(request_list.requests.order_by("id"))
    assert len(requests) == 4
    assert all(r.status == "Under Review" for r in requests)
    assert all(r.requested_by == admin_user for r in requests)
    assert all(r.fulfillment_type == "Internal Synthesis" for r in requests)
    assert requests[0].substance_id == substance.id
    assert requests[0].amount == Decimal("50.000")
    assert requests[0].priority == "Low"
    assert requests[1].is_mixture and requests[1].mixture_id == mixture.id
    assert requests[1].priority == "High"
    assert requests[2].substance.molecule.inchi_key
    assert requests[2].substance_id != requests[3].substance_id
    # history is saved for each request, which is needed for `status_age`
    assert InventoryRequest.history.filter(request_list=request_list).count() == 4

    # nothing is saved if any row is invalid
    num_lists = InventoryRequestList.objects.count()
    num_requests = InventoryRequest.objects.count()
    with pytest.raises(ValidationError) as error:
        InventoryRequestList.create_with_requests(
            title="Bad list",
            rows=[dict(item="c1ccccc1"), dict(item="not a smiles")],
            submitted_by=admin_user,
        )
    assert error.value.messages[0].startswith("Row 2:")
    assert InventoryRequestList.objects.count() == num_lists
    assert InventoryRequest.objects.count() == num_requests

    # warnings (e.g. items with open requests) must be allowed
    with pytest.raises(ValidationError):
        InventoryRequestList.create_with_requests(
            title="Remakes", rows=[dict(item="BCD-012-0001")]
        )
    request_list = InventoryRequestList.create_with_requests(
        title="Remakes", rows=[dict(item="BCD-012-0001")], allow_warnings=True
    )
    assert request_list.requests.count() == 1

    # a title is required
    with pytest.raises(ValidationError):
        InventoryRequestList.create_with_requests(title=" ", rows=[dict(item="CCN")])


@pytest.mark.django_db
def test_request_list_rollup():
    substance = Substance.objects.create(id="BCD-012-0001")
    empty = InventoryRequestList.objects.create(title="empty")
    lists = {}
    for title, statuses in [
        ("open", ["Completed", "In Progress"]),
        ("completed", ["Completed", "Completed"]),
        ("closed", ["Completed", "Failed"]),
    ]:
        lists[title] = InventoryRequestList.objects.create(title=title)
        for status in statuses:
            InventoryRequest.objects.create(
                substance=substance, status=status, request_list=lists[title]
            )

    rollups = {
        row["title"]: row
        for row in InventoryRequestList.get_web_queryset().values(
            "title", "num_requests", "num_open", "num_completed", "num_closed", "status"
        )
    }
    assert rollups["empty"]["status"] == "Empty"
    assert rollups["open"]["status"] == "Open"
    assert rollups["open"]["num_open"] == 1
    assert rollups["completed"]["status"] == "Completed"
    assert rollups["completed"]["num_completed"] == 2
    assert rollups["closed"]["status"] == "Closed"
    assert rollups["closed"]["num_closed"] == 1

    results = InventoryRequestList.filter_from_config(
        filters=dict(status="Open"), paginate=False, use_web_queryset=True
    )
    assert [r.id for r in results] == [lists["open"].id]
    assert empty.id not in [r.id for r in results]


@pytest.mark.django_db
def test_request_list_views(admin_client, admin_user):
    request_list = InventoryRequestList.create_with_requests(
        title="Round 3 targets",
        rows=[dict(item="CCO"), dict(item="CCN")],
        submitted_by=admin_user,
    )
    table_name = InventoryRequestList.table_name

    response = admin_client.get(reverse("data_explorer:table", args=[table_name]))
    assert response.status_code == 200
    assert "Round 3 targets" in response.content.decode()

    response = admin_client.get(
        reverse("data_explorer:table-entry-new", args=[table_name])
    )
    assert response.status_code == 200

    response = admin_client.get(
        reverse("data_explorer:table-entry", args=[table_name, request_list.id])
    )
    assert response.status_code == 200
    assert response.context["table_entry"].num_requests == 2
    content = response.content.decode()
    for request in request_list.requests.all():
        assert request.display_id in content

    # the requests of a list can be filtered by it, and new ones added to it
    response = admin_client.get(
        reverse("data_explorer:table", args=[InventoryRequest.table_name]),
        {"request_list_id": request_list.id},
    )
    assert response.status_code == 200
    assert response.context["total"] == 2
    response = admin_client.get(
        reverse("data_explorer:table-entry-new", args=[InventoryRequest.table_name]),
        {"request_list_id": request_list.id},
    )
    assert response.status_code == 200


def get_component_from_page(content: str, component_class) -> HtmxComponent:
    """
    Gives the component of the given class that was rendered on a page.
    """
    for component_id in re.findall(r'<div id="([^"]+)" style="overflow-anchor', content):
        component = HtmxComponent.from_cache(component_id)
        if isinstance(component, component_class):
            return component
    raise ValueError(f"No {component_class.__name__} found on the page")


@pytest.mark.django_db
def test_request_list_form(admin_client):
    Substance.objects.create(id="BCD-012-0001")
    response = admin_client.get(
        reverse("data_explorer:table-entry-new", args=[InventoryRequestList.table_name])
    )
    component = get_component_from_page(
        response.content.decode(), InventoryRequestListComponent
    )

    def call(method_name: str = None, **data):
        args = [component.component_id] + ([method_name] if method_name else [])
        url_name = "htmx:component_method" if method_name else "htmx:component"
        return admin_client.post(reverse(url_name, args=args), data)

    # pasted lines without a header give the item, amount, and units
    response = call("load_paste", paste_text="BCD-012-0001, 50, mg\nCCO")
    assert response.status_code == 200
    assert [row["item"] for row in component.rows] == ["BCD-012-0001", "CCO"]
    assert component.form_data["paste_text"] == ""

    # Excel's CSV files are often sent as "application/vnd.ms-excel"
    file = SimpleUploadedFile(
        "items.csv",
        b"SMILES,Catalog Number,Units\nCCN,00123,ML\n",
        content_type="application/vnd.ms-excel",
    )
    response = call(request_file=file)
    assert response.status_code == 200
    assert component.action_message == "Added 1 row from 'items.csv'."
    new_row = component.rows[-1]
    assert new_row["supplier_catalog_number"] == "00123"
    assert new_row["amount_units"] == "ml"

    # the substance already has an open request after this, so the list
    # needs to be saved anyway
    InventoryRequest.objects.create(substance_id="BCD-012-0001", status="On Hold")
    response = call("submit_form", title="Form list")
    assert response.status_code == 200
    assert "HX-Redirect" not in response
    assert InventoryRequestList.objects.filter(title="Form list").count() == 0

    response = call("submit_form_with_warnings", title="Form list")
    request_list = InventoryRequestList.objects.get(title="Form list")
    assert response["HX-Redirect"].endswith(f"/{request_list.id}/")
    assert request_list.requests.count() == 3


@pytest.mark.django_db
def test_update_many_requests(admin_user):
    substance = Substance.objects.create(id="BCD-012-0001")
    request_list = InventoryRequestList.objects.create(title="list")
    requests = [
        InventoryRequest.objects.create(
            substance=substance,
            status="Under Review",
            priority="Low",
            request_list=request_list,
            comments=comments,
        )
        for comments in [None, "first note"]
    ]

    # the table's filters are in the URL, and must not be saved to the requests
    request = RequestFactory().get(
        f"/data/InventoryRequest/?request_list_id={request_list.id}&priority=%22Low%22"
    )
    request.user = admin_user
    component = InventoryRequestComponent(
        component_type="update_many",
        redirect_mode="no_redirect",
        request=request,
    )
    assert "priority" not in component.form_data

    component.entry_ids_to_update = [r.id for r in requests]
    component.form_data.update(status="Approved", comments="approved together")
    component.submit_form()
    assert not component.form_errors

    for entry in requests:
        entry.refresh_from_db()
        assert entry.status == "Approved"
        assert entry.priority == "Low"
        assert entry.history.count() == 2
    assert requests[0].comments == "approved together"
    assert requests[1].comments == "first note\n\napproved together"
