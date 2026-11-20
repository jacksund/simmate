import math
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, Count, F, Q, Value, When
from simple_history.utils import bulk_create_with_history

from simmate.apps.project_management.models import Project
from simmate.database.core import DatabaseTable, table_column

from .inventory_request import InventoryRequest
from .substance import Substance


def _to_text(value) -> str:
    """
    Converts a cell from a file, form, or script to clean text. Empty cells
    (None or NaN) give "", whole-number floats lose their ".0" (e.g. a catalog
    number read as 123.0), and dates are given as "YYYY-MM-DD".
    """
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, datetime):
        # e.g. dates from Excel are read as midnight of that day
        if value.time() == datetime.min.time():
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _match_option(value: str, options: list[str]) -> str | None:
    """
    Gives the option that matches the value, ignoring case (e.g. "MG" gives
    "mg"), or None if there is no match.
    """
    return {option.lower(): option for option in options}.get(value.lower())


class InventoryRequestList(DatabaseTable):
    """
    A group of inventory requests that were submitted together, such as a
    round of 40 targets for a project or a batch of items to order from one
    supplier. Lists are identified by their `display_id` (e.g. "RL-12").

    A list is only a header (e.g. its `title`), and its requests are available
    via `requests`. Values shared by the requests (e.g. the project, priority,
    or supplier) are copied onto each request when the list is made, so every
    request can still be searched and edited on its own. The status of a list
    is worked out from its requests (see `get_web_queryset`).

    Lists are made with `create_with_requests`, which is used by both the
    website's form and scripts. For example:

    ``` python
    from simmate.apps.inventory_management.models import InventoryRequestList

    request_list = InventoryRequestList.create_with_requests(
        title="Round 3 targets",
        rows=[
            dict(item="BCD-012-3456", amount="50", amount_units="mg"),
            dict(item="CCO", priority="High"),  # new SMILES are registered
        ],
        shared=dict(fulfillment_type="Internal Synthesis", priority="Medium"),
        submitted_by=user,
    )
    ```
    """

    class Meta:
        db_table = "inventory_management__inventory_request_lists"
        verbose_name = "Inventory Request List"

    id_prefix = "RL"
    """
    The static prefix of every list's `display_id` (e.g. "RL-12").
    """

    # -------------------------------------------------------------------------

    title = table_column.CharField(max_length=100, blank=True, null=True)
    """
    A short name for the list (e.g. "Round 3 targets" or "Sigma order").
    This is required when a list is made.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    What the list is for (e.g. the design rationale of a round of targets).
    Notes about a single item go in that request's `comments` instead.
    """

    submitted_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="submitted_inventory_request_lists",
        blank=True,
        null=True,
    )
    """
    The user that submitted the list, which is set automatically when the
    list is made.
    """

    project = table_column.ForeignKey(
        "project_management.Project",
        on_delete=table_column.SET_NULL,
        related_name="inventory_request_lists",
        blank=True,
        null=True,
    )
    """
    The project that the list is for, if any. This is copied onto each request
    when the list is made, so changing it later does not update the requests.
    """

    # -------------------------------------------------------------------------

    # Columns accepted for each row of a new list. Rows are given as text
    # (e.g. from a CSV file), and blank cells are filled in with the shared
    # value of that column (if any).

    max_requests: int = 100
    """
    The most requests that can be made in one list.
    """

    row_columns: list[str] = [
        "item",
        "amount",
        "amount_units",
        "fulfillment_type",
        "priority",
        "needed_by",
        "supplier",
        "supplier_catalog_number",
        "estimated_cost",
        "comments",
    ]
    """
    The columns of each row, where `item` is a substance ID (e.g.
    "BCD-012-3456"), mixture ID (e.g. "BCDF-123"), or SMILES. The rest match
    the columns of `InventoryRequest` (see `value_columns`).
    """

    value_columns: list[str] = row_columns[1:]
    """
    The `row_columns` other than `item`, which are columns of `InventoryRequest`
    and can also be given as shared values.
    """

    shared_columns: dict[str, type] = {
        "project_id": Project,
        "requested_by_id": User,
        "assigned_to_id": User,
    }
    """
    Columns that can only be given once for the whole list (i.e. not per row),
    along with the table that each must be an ID of. These are copied onto
    every request, along with any shared `value_columns`.
    """

    column_aliases: dict[str, str] = {
        "substance": "item",
        "substance_id": "item",
        "mixture": "item",
        "mixture_id": "item",
        "smiles": "item",
        "compound": "item",
        "id": "item",
        "units": "amount_units",
        "unit": "amount_units",
        "fulfillment": "fulfillment_type",
        "vendor": "supplier",
        "catalog_number": "supplier_catalog_number",
        "product_number": "supplier_catalog_number",
        "cost": "estimated_cost",
        "comment": "comments",
        "notes": "comments",
    }
    """
    Other accepted names for the `row_columns` in file headers. Headers are
    also matched ignoring case, spaces, and punctuation (e.g. "Amount Units"
    gives `amount_units`).
    """

    option_columns: dict[str, list[str]] = {
        "amount_units": InventoryRequest.amount_units_options,
        "fulfillment_type": InventoryRequest.fulfillment_type_options,
        "priority": InventoryRequest.priority_options,
    }
    """
    The `row_columns` whose values must be one of a list of options.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        # The status of a list comes from its requests:
        #   - "Open" if any request is still open (e.g. "In Progress")
        #   - "Completed" if every request is completed
        #   - "Closed" if no request is open, but some did not complete
        #   - "Empty" if it has no requests
        return (
            cls.objects.select_related("submitted_by", "project")
            .annotate(
                num_requests=Count("requests"),
                num_open=Count(
                    "requests",
                    filter=Q(
                        requests__status__in=InventoryRequest.open_status_options
                    ),
                ),
                num_completed=Count(
                    "requests",
                    filter=Q(
                        requests__status=InventoryRequest.status_completed_name
                    ),
                ),
            )
            .annotate(
                num_closed=F("num_requests") - F("num_open") - F("num_completed"),
                status=Case(
                    When(num_requests=0, then=Value("Empty")),
                    When(num_open__gt=0, then=Value("Open")),
                    When(num_completed=F("num_requests"), then=Value("Completed")),
                    default=Value("Closed"),
                ),
            )
        )

    # -------------------------------------------------------------------------

    # MAKING NEW LISTS

    @classmethod
    def get_column_name(cls, header: str) -> str | None:
        """
        Gives the row column for a header name (e.g. "Amount Units" or
        "units" give "amount_units"), or None if it is not a known column.
        Headers are matched ignoring case, spaces, and punctuation, and can
        be any of the `column_aliases`.
        """
        name = re.sub(r"[^a-z0-9]+", "_", _to_text(header).lower()).strip("_")
        name = cls.column_aliases.get(name, name)
        return name if name in cls.row_columns else None

    @classmethod
    def parse_table(cls, columns: list, records: list[list]) -> list[dict]:
        """
        Converts a table (e.g. from a CSV file or pasted text) into rows for
        `check_rows`. Column names are matched to `row_columns` (see
        `column_aliases`), option values are given their listed spelling
        (e.g. "MG" gives "mg"), and fully blank records are dropped.

        Args:
            columns: The column names (i.e. the header).
            records: The values of each record, in the same order as `columns`.

        Returns:
            One dictionary per record, which maps each column to its text.

        Raises:
            ValueError: if a column is unknown or repeated, if there is no
                `item` column, or if a record has more values than columns.
        """
        names = []  # None marks columns that have no header
        for column in columns:
            text = _to_text(column)
            # pandas names columns without a header "Unnamed: 3"
            if not text or re.fullmatch(r"Unnamed: \d+", text):
                names.append(None)
                continue
            name = cls.get_column_name(text)
            if not name:
                raise ValueError(
                    f"Unknown column '{text}'. Columns must be named: "
                    f"{', '.join(cls.row_columns)}."
                )
            if name in names:
                raise ValueError(f"More than one column is for '{name}'.")
            names.append(name)
        if "item" not in names:
            raise ValueError(
                "An 'item' column is required, giving the substance ID, "
                "mixture ID, or SMILES of each request."
            )

        rows = []
        for number, record in enumerate(records, start=1):
            cells = [_to_text(cell) for cell in record]
            extra_cells = cells[len(names) :]
            cells = cells[: len(names)] + [""] * (len(names) - len(cells))
            if any(extra_cells) or any(
                cell for name, cell in zip(names, cells) if name is None
            ):
                raise ValueError(
                    f"Row {number} has a value in a column without a header."
                )
            row = {name: cell for name, cell in zip(names, cells) if name}
            if not any(row.values()):
                continue
            for column, options in cls.option_columns.items():
                if row.get(column):
                    row[column] = _match_option(row[column], options) or row[column]
            rows.append(row)
        return rows

    @classmethod
    def _clean_values(cls, cells: dict[str, str]) -> tuple[dict, list[str]]:
        """
        Converts the text of request columns (any of `value_columns`) to their
        database values. Blank and invalid cells give None. Limits (e.g.
        lengths) come from the columns of `InventoryRequest`.

        Returns:
            The cleaned values, and a message for each value that is invalid.
        """
        values = dict.fromkeys(cells)
        errors = []
        for column, text in cells.items():
            text = _to_text(text)
            if not text:
                continue

            if column == "amount":
                field = InventoryRequest._meta.get_field(column)
                try:
                    value = Decimal(text)
                except InvalidOperation:
                    value = Decimal("NaN")
                if not value.is_finite() or value <= 0:
                    errors.append(f"amount must be a number above 0 (got '{text}').")
                elif value >= 10 ** (field.max_digits - field.decimal_places):
                    errors.append(f"amount is too large (got '{text}').")
                else:
                    values[column] = value.quantize(Decimal(10) ** -field.decimal_places)

            elif column == "estimated_cost":
                try:
                    value = float(text)
                except ValueError:
                    value = math.nan
                if not math.isfinite(value) or value < 0:
                    errors.append(
                        f"estimated_cost must be a number of USD (got '{text}')."
                    )
                else:
                    values[column] = value

            elif column == "needed_by":
                try:
                    values[column] = datetime.fromisoformat(text).date()
                except ValueError:
                    errors.append(
                        f"needed_by must be a date like 2026-12-31 (got '{text}')."
                    )

            elif column in cls.option_columns:
                options = cls.option_columns[column]
                values[column] = _match_option(text, options)
                if not values[column]:
                    errors.append(
                        f"{column} must be one of: {', '.join(options)} "
                        f"(got '{text}')."
                    )

            else:
                max_length = InventoryRequest._meta.get_field(column).max_length
                if max_length and len(text) > max_length:
                    errors.append(f"{column} must be {max_length} characters or fewer.")
                else:
                    values[column] = text

        return values, errors

    @classmethod
    def check_rows(
        cls,
        rows: list[dict],
        shared: dict = None,
        resolved: dict[str, dict] = None,
    ) -> tuple[list[dict], list[str], list[str]]:
        """
        Checks the rows of a new list, without saving anything.

        Args:
            rows: One dictionary per request, with keys from `row_columns`
                and text values (e.g. from `parse_table`).
            shared: Values for the whole list, with keys from `shared_columns`
                and `value_columns`. These are used for any row whose cell is
                blank. Rows can't clear a shared value.
            resolved: A cache of items looked up with
                `InventoryRequest.resolve_items`, which saves repeat queries
                (e.g. as a form is edited). Missing items are looked up and
                added to it.

        Returns:
            A tuple of:
                - the checked rows, which give the `number` (counting from 1),
                  `cells` (the text given), `status` ("substance", "mixture",
                  "new", "invalid", or "blank"), `info` (from `resolve_items`),
                  `values` (the request's columns, including shared values),
                  plus row-specific `errors`, `warnings`, and `notes`
                - all errors, which must be fixed before saving
                - all warnings, which must be confirmed before saving (e.g. an
                  item listed twice or that already has an open request)
        """
        shared = shared or {}
        errors = []
        warnings = []

        # Shared values
        shared_values, shared_errors = cls._clean_values(
            {column: shared.get(column) for column in cls.value_columns}
        )
        errors += [f"Shared {error}" for error in shared_errors]
        for column, table in cls.shared_columns.items():
            value = _to_text(shared.get(column))
            if value and (
                not value.isdigit() or not table.objects.filter(id=value).exists()
            ):
                errors.append(
                    f"Shared {column} must be the ID of a {table.__name__}."
                )

        # Items are looked up together, reusing any that were given
        resolved = {} if resolved is None else resolved
        items = {_to_text(row.get("item")) for row in rows} - {""}
        missing = items - resolved.keys()
        if missing:
            resolved.update(InventoryRequest.resolve_items(list(missing)))

        checked_rows = []
        first_rows = {}  # substance or mixture --> the first row number it is in
        for number, row in enumerate(rows, start=1):
            cells = {column: _to_text(row.get(column)) for column in cls.row_columns}
            checked = dict(
                number=number,
                cells=cells,
                status="blank",
                info=None,
                values=None,
                errors=[],
                warnings=[],
                notes=[],
            )
            checked_rows.append(checked)
            if not any(cells.values()):
                continue

            unknown = sorted(set(row) - set(cls.row_columns))
            if unknown:
                checked["errors"].append(f"has unknown columns: {', '.join(unknown)}.")

            # Item
            item = cells["item"]
            if not item:
                checked["status"] = "invalid"
                checked["errors"].append("has no item.")
            else:
                info = dict(resolved[item])  # copied so that it can be updated
                checked["info"] = info
                if info["kind"] == "invalid":
                    checked["status"] = "invalid"
                    checked["errors"].append(f"'{item}' {info['error']}.")
                elif info["kind"] == "mixture":
                    checked["status"] = "mixture"
                elif info["kind"] == "substance" or info["substance_id"]:
                    checked["status"] = "substance"
                else:
                    checked["status"] = "new"
                    checked["notes"].append("will be registered as a new substance.")

                substance_id = info["substance_id"]
                if info["merged_from"]:
                    checked["notes"].append(
                        f"{info['merged_from']} now redirects to {substance_id}."
                    )
                if info["kind"] == "smiles" and substance_id:
                    checked["notes"].append(f"matches {substance_id}.")

                if checked["status"] != "invalid":
                    # the same item can be given in different ways (e.g. by
                    # ID and by SMILES, or as two SMILES)
                    if substance_id:
                        key = ("substance", substance_id)
                    elif info["mixture_id"]:
                        key = ("mixture", info["mixture_id"])
                    else:
                        key = ("inchi_key", info["inchi_key"])
                    if key in first_rows:
                        checked["warnings"].append(
                            f"is the same item as row {first_rows[key]}."
                        )
                    else:
                        first_rows[key] = number
                if info["open_request_ids"]:
                    checked["warnings"].append(
                        "already has open request(s): "
                        f"{', '.join(info['open_request_ids'])}."
                    )

            # Request columns, where blank cells use the shared value
            values, value_errors = cls._clean_values(
                {column: cells[column] for column in cls.value_columns}
            )
            checked["errors"] += value_errors
            for column, value in shared_values.items():
                if values[column] is None:
                    values[column] = value
            if values["amount"] is not None and not values["amount_units"]:
                checked["errors"].append("has an amount but no amount_units.")
            checked["values"] = values

            errors += [f"Row {number}: {message}" for message in checked["errors"]]
            warnings += [f"Row {number}: {message}" for message in checked["warnings"]]

        num_requests = len([row for row in checked_rows if row["status"] != "blank"])
        if not num_requests:
            errors.append("Add at least one item to request.")
        elif num_requests > cls.max_requests:
            errors.append(
                f"A list can have at most {cls.max_requests} requests "
                f"(got {num_requests}). Split the items into more than one list."
            )

        return checked_rows, errors, warnings

    @classmethod
    def create_with_requests(
        cls,
        title: str,
        rows: list[dict],
        shared: dict = None,
        description: str = None,
        submitted_by: User = None,
        allow_warnings: bool = False,
        resolved: dict[str, dict] = None,
    ) -> "InventoryRequestList":
        """
        Makes a new list along with one request per row. Everything is checked
        first (see `check_rows`), and then all of it is saved together, so
        either every request is made or none are.

        Substance and mixture IDs must already be registered, while SMILES are
        registered as new substances (if needed) with a single call to
        `SubstanceDatastore.get_or_create_ids`. New requests start as
        "Under Review" and are requested by the `submitted_by` user unless
        `shared` gives a `requested_by_id`.

        Args:
            title: The name of the new list.
            rows: The requests to make (see `check_rows`).
            shared: Values for every request (see `check_rows`).
            description: What the list is for.
            submitted_by: The user that is making the list.
            allow_warnings: Whether to save even if there are warnings (e.g.
                an item that already has an open request).
            resolved: Items that were just looked up (see `check_rows`). Leave
                as None to look up every item.

        Returns:
            The new list, whose requests are available via `requests`.

        Raises:
            ValidationError: with all of the messages, if anything is invalid
                (or if there are warnings and `allow_warnings` is False).
        """
        from ..datastores import SubstanceDatastore

        shared = shared or {}
        checked_rows, errors, warnings = cls.check_rows(rows, shared, resolved)
        title = _to_text(title)
        max_length = cls._meta.get_field("title").max_length
        if not title:
            errors.insert(0, "A title is required.")
        elif len(title) > max_length:
            errors.insert(0, f"The title must be {max_length} characters or fewer.")
        if not allow_warnings:
            errors += warnings
        if errors:
            raise ValidationError(errors)

        rows_to_save = [row for row in checked_rows if row["status"] != "blank"]
        submitted_by_id = submitted_by.id if submitted_by else None
        shared_ids = {
            column: int(_to_text(shared[column])) if shared.get(column) else None
            for column in cls.shared_columns
        }

        with transaction.atomic():
            # Substances that are only in the datastore are copied into the
            # database, so that requests can link to them
            existing_ids = [
                row["info"]["substance_id"]
                for row in rows_to_save
                if row["info"]["kind"] == "substance"
            ]
            if existing_ids:
                try:
                    Substance._hydrate(existing_ids)
                except ValueError as error:
                    raise ValidationError(str(error))

            # This is the single entry point for registering substances, and
            # it gives the existing ID of any SMILES already registered
            smiles_rows = [
                row for row in rows_to_save if row["info"]["kind"] == "smiles"
            ]
            if smiles_rows:
                substance_ids = SubstanceDatastore.get_or_create_ids(
                    [
                        dict(
                            molecule=row["cells"]["item"],
                            registered_by_id=submitted_by_id,
                        )
                        for row in smiles_rows
                    ]
                )
                for row, substance_id in zip(smiles_rows, substance_ids):
                    row["info"]["substance_id"] = substance_id

            request_list = cls.objects.create(
                title=title,
                description=_to_text(description) or None,
                submitted_by=submitted_by,
                project_id=shared_ids["project_id"],
            )
            requests = [
                InventoryRequest(
                    request_list=request_list,
                    status="Under Review",
                    is_mixture=row["info"]["kind"] == "mixture",
                    substance_id=row["info"]["substance_id"],
                    mixture_id=row["info"]["mixture_id"],
                    submitted_by=submitted_by,
                    requested_by_id=shared_ids["requested_by_id"] or submitted_by_id,
                    assigned_to_id=shared_ids["assigned_to_id"],
                    project_id=shared_ids["project_id"],
                    **row["values"],
                )
                for row in rows_to_save
            ]
            # unlike `bulk_create`, this also saves each request's history,
            # which is needed for its `status_age`
            bulk_create_with_history(
                requests,
                InventoryRequest,
                default_user=submitted_by,
            )

        return request_list
