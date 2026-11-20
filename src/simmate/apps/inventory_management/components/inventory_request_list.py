from collections import Counter
from itertools import zip_longest

from django.core.exceptions import ValidationError
from django.db.models import Count

from simmate.apps.project_management.components.mixins import ProjectInput
from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

from ..models import InventoryRequest, InventoryRequestList


class InventoryRequestListComponent(TableComponent, UserInput, ProjectInput):
    table = InventoryRequestList

    display_name = "Inventory Request Lists"
    description_short = (
        "Groups of inventory requests that were submitted together, such as a "
        "round of targets for a project or a batch of items to order."
    )

    template_names = {
        "dashboard": "inventory_management/inventory_request_list/dashboard.html",
        "entries": "inventory_management/inventory_request_list/table.html",
        "entry": "inventory_management/inventory_request_list/view.html",
        "create": "inventory_management/inventory_request_list/form.html",
        "update": "inventory_management/inventory_request_list/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "create",
        "update",
    ]

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view, any signed-in user can make a list, and admins or
        # the submitter can edit it
        if component_type in ["dashboard", "entries", "entry"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or component_type == "create":
            return True
        if component_type == "update":
            return table_entry is not None and user.id == table_entry.submitted_by_id
        return False

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(
        cls, request, table_entry: InventoryRequestList
    ) -> dict:
        # the entry page loads the row without `get_web_queryset`, so it is
        # reloaded with its counts and status (and replaces the given entry)
        table_entry = InventoryRequestList.get_web_queryset().get(id=table_entry.id)
        status_counts = (
            InventoryRequest.objects.filter(request_list=table_entry)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("-count", "status")
        )
        limit = cls.max_requests
        inventory_requests = (
            InventoryRequest.get_web_queryset()
            .filter(request_list=table_entry)
            .order_by("id")[:limit]
        )
        return {
            "table_entry": table_entry,
            "status_counts": list(status_counts),
            "inventory_requests": inventory_requests,
            "inventory_requests__truncated": table_entry.num_requests > limit,
        }

    # -------------------------------------------------------------------------

    # CREATE

    # A new list is filled in as a table with one row per request. Rows can be
    # loaded from a CSV/Excel file or pasted text, and then edited by hand.
    # Each column of the table is kept as a list of str in the form data
    # (e.g. `row__item` and `row__amount`), which are read together as `rows`.
    # Shared values (e.g. `priority`) are used for any row whose cell is left
    # blank. Rows are checked as they are edited (see `preview`), and the
    # whole list is saved at once by `InventoryRequestList.create_with_requests`.

    required_inputs = ["title"]

    row_columns = InventoryRequestList.row_columns

    max_requests = InventoryRequestList.max_requests

    template_csv = ",".join(row_columns) + "\n"
    """
    An empty CSV file with the accepted columns, which users can download
    and fill in.
    """

    # options for the shared values, which are columns of InventoryRequest
    # rather than this table
    amount_units_options = InventoryRequest.amount_units_options
    fulfillment_type_options = InventoryRequest.fulfillment_type_options
    priority_options = InventoryRequest.priority_options

    post_data_mappings = {
        # each row of the table gives one entry to these lists. They stay as
        # str so that blank and invalid cells can be shown and checked
        **{f"row__{column}": list[str] for column in InventoryRequestList.row_columns},
        # these are otherwise parsed into other types (e.g. "123" to an int)
        "title": str,
        "description": str,
        "paste_text": str,
        "amount": str,
        "estimated_cost": str,
        "needed_by": str,
        "supplier": str,
        "comments": str,
    }

    # the file is read by `on_change_hook__request_file`, without guessing
    # the type of each column
    raw_file_inputs = ["request_file"]

    resolved_items: dict = None
    """
    Items of the table that were already looked up (see
    `InventoryRequest.resolve_items`), so that only new items are looked up
    as the table is edited.
    """

    is_warnings_confirmed: bool = False
    """
    Whether the user chose to save the list even though it has warnings (see
    `submit_form_with_warnings`).
    """

    def mount_for_create(self):
        self.set_rows([])
        self.update_form("paste_text", "")
        # most people request material for themselves, but this can be changed
        # to submit a list on behalf of someone else
        self.update_form("requested_by_id", self.request.user.id)
        self.resolved_items = {}

    @property
    def rows(self) -> list[dict]:
        """
        The rows of the table, as dictionaries of `row_columns` to their text.
        """
        columns = [self.form_data.get(f"row__{c}") or [] for c in self.row_columns]
        return [
            dict(zip(self.row_columns, cells))
            for cells in zip_longest(*columns, fillvalue="")
        ]

    def set_rows(self, rows: list[dict]):
        """
        Replaces all rows of the table.
        """
        for column in self.row_columns:
            self.form_data[f"row__{column}"] = [
                row.get(column) or "" for row in rows
            ]

    @property
    def shared_values(self) -> dict:
        """
        The values given for the whole list (see `InventoryRequestList.check_rows`).
        """
        columns = [
            *InventoryRequestList.shared_columns,
            *InventoryRequestList.value_columns,
        ]
        return {column: self.form_data.get(column) for column in columns}

    @property
    def preview(self) -> dict:
        """
        The result of checking every row (see `InventoryRequestList.check_rows`).
        Only items that weren't seen before are looked up (see `resolved_items`).
        """
        checked_rows, errors, warnings = InventoryRequestList.check_rows(
            self.rows,
            self.shared_values,
            resolved=self.resolved_items,
        )
        return dict(
            rows=checked_rows,
            errors=errors,
            warnings=warnings,
            status_counts=Counter(
                row["status"] for row in checked_rows if row["status"] != "blank"
            ),
        )

    # -------------------------------------------------------------------------

    # Editing the rows

    def add_row(self):
        self.set_rows(self.rows + [{}])

    def remove_row(self, index: int):
        rows = self.rows
        if 0 <= index < len(rows):
            rows.pop(index)
        self.set_rows(rows)

    def clear_rows(self):
        self.set_rows([])

    def _add_rows(self, new_rows: list[dict], source: str):
        """
        Adds rows to the end of the table, in place of any blank rows.
        """
        rows = [row for row in self.rows if any(v.strip() for v in row.values())]
        total = len(rows) + len(new_rows)
        if total > self.max_requests:
            self.action_error = (
                f"Adding {len(new_rows)} rows from {source} would give {total} "
                f"requests, but a list can have at most {self.max_requests}."
            )
            return
        self.set_rows(rows + new_rows)
        plural = "s" if len(new_rows) != 1 else ""
        self.action_message = f"Added {len(new_rows)} row{plural} from {source}."

    def load_paste(self):
        """
        Adds a row for each line of the pasted text. Cells can be separated by
        tabs (e.g. cells copied from Excel) or commas. The first line can be a
        header that names the columns. Otherwise, each line gives an item and
        (optionally) its amount and amount units.
        """
        text = self.form_data.get("paste_text") or ""
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            self.action_error = "Paste one item per line first."
            return

        delimiter = "\t" if any("\t" in line for line in lines) else ","
        records = [[cell.strip() for cell in line.split(delimiter)] for line in lines]
        is_header = all(
            InventoryRequestList.get_column_name(cell) for cell in records[0] if cell
        )
        try:
            if is_header:
                rows = InventoryRequestList.parse_table(records[0], records[1:])
            else:
                columns = ["item", "amount", "amount_units"]
                if max(len(record) for record in records) > len(columns):
                    raise ValueError(
                        "Lines without a header can only give the item, amount, "
                        "and amount units. Add a header line (e.g. "
                        "'item,amount,amount_units,priority') to give other columns."
                    )
                rows = InventoryRequestList.parse_table(columns, records)
        except ValueError as error:
            self.action_error = str(error)
            return
        if not rows:
            self.action_error = "The pasted text has no items."
            return

        self._add_rows(rows, "the pasted text")
        if not self.action_error:
            self.form_data["paste_text"] = ""

    def on_change_hook__request_file(self):
        # removed right away, so that the file isn't kept in the cached
        # component and the same file can be uploaded again
        file = self.form_data.pop("request_file", None)
        if file is None:
            return
        try:
            # cells are kept as text (e.g. catalog numbers keep leading zeros)
            df = self.read_table_file(file, as_text=True)
            rows = InventoryRequestList.parse_table(df.columns, df.values.tolist())
        except ValueError as error:
            self.action_error = f"Could not load '{file.name}': {error}"
            return
        if not rows:
            self.action_error = f"'{file.name}' has no items."
            return
        self._add_rows(rows, f"'{file.name}'")

    # -------------------------------------------------------------------------

    # Saving

    def check_form_for_create(self):
        # Other checks of the list itself (e.g. the title's length) are made
        # by `create_with_requests` when saving
        self.check_required_inputs()

        # The final check is made with fresh data (e.g. requests that were
        # opened since the items were first looked up). These lookups are
        # then reused when saving.
        self.resolved_items = {}
        preview = self.preview

        errors = preview["errors"]
        max_errors = 10
        self.form_errors += errors[:max_errors]
        if len(errors) > max_errors:
            self.form_errors.append(
                f"...and {len(errors) - max_errors} more errors (see the rows below)."
            )
        if preview["warnings"] and not errors and not self.is_warnings_confirmed:
            self.form_errors.append(
                f"There are {len(preview['warnings'])} warnings (see the rows "
                "below). Fix them, or save anyway if they are expected."
            )

    def unmount_for_create(self):
        return  # the list is made by `create_with_requests` in one step

    def save_to_db_for_create(self):
        if self._db_save_completed:
            # might be a duplicate call (e.g. a double click) so we exit
            raise Exception(
                "This list was already saved. You might have a race condition."
            )
        self.table_entry = InventoryRequestList.create_with_requests(
            title=self.form_data.get("title"),
            rows=self.rows,
            shared=self.shared_values,
            description=self.form_data.get("description"),
            submitted_by=self.request.user,
            allow_warnings=self.is_warnings_confirmed,
            resolved=self.resolved_items,
        )
        self._db_save_completed = True

    def submit_form(self):
        try:
            return super().submit_form()
        except ValidationError as error:
            # e.g. an item was changed by someone else after it was checked.
            # Nothing was saved, so the form is shown again with the errors.
            self.form_errors = error.messages
            return None

    def submit_form_with_warnings(self):
        """
        Saves the list even if it has warnings (e.g. an item that already has
        an open request). Errors still stop the list from being saved.
        """
        self.is_warnings_confirmed = True
        try:
            return self.submit_form()
        finally:
            self.is_warnings_confirmed = False

    # -------------------------------------------------------------------------

    # UPDATE

    # the requests of a list are edited on their own (or in bulk from the
    # InventoryRequest table), so only the list's header is edited here
    mount_for_update_columns = [
        "title",
        "description",
        "project_id",
    ]

    def check_form_for_update(self):
        # the create checks are only for making new lists
        self.check_required_inputs()

    def save_to_db_for_update(self):
        # The default repeats `save_to_db_for_create`, which makes a new list
        # here. Updates only save the list itself.
        super().save_to_db_for_create()
