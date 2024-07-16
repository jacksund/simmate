from django.shortcuts import redirect
from django_unicorn.components import UnicornView

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, FilteredScope, table_column

# TODO: move to util and combine with var used in views.py
# TODO: include all ORM models automatically
# import django.apps
# django.apps.apps.get_models()
ALL_API_TABLES = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for table_name in settings.website.data
}


class ApiFilterView(UnicornView):

    template_name = "data_explorer_dev/api_filter.html"

    parent_url = None

    def mount(self):

        # BUG: filters carry over across refreshes...?
        self.filters = []

        # needed for resubmission
        self.parent_url = self.request.path

        # load table
        table = self._determine_table()
        self.table_name = table.table_name

        # load url args + starting filters
        url_config = table._parse_request_get(self.request)
        self._load_filters(url_config.get("filters", {}))

        # populate rest of form starting fields
        self._set_column_options()

    # -------------------------------------------------------------------------

    table_name = None

    def _get_base_table(self):
        return ALL_API_TABLES[self.table_name]

    def _determine_table(self):
        """
        Given a request, this will return the database table that corresponds to
        the webpage. For example, the request for "/data/MatprojStructure/"
        would load & return the "MatprojStructure" class
        """
        # BUG: hardcoded for early testing
        if self.request.path == "/apps/discovery_lab/dev_api/":
            return ALL_API_TABLES["CortevaTarget"]
        # TODO: once this is in the data_explorer app
        # print(self.kwargs) --> should give table name
        # table = ALL_API_TABLES[table_name]

    # -------------------------------------------------------------------------

    column_selected = None
    column_parents = []
    column_options = []
    column_options_hash = None

    def _get_column_type(self):
        column = self._get_column()
        column_type = type(column)
        return column_type

    def _get_column(self):
        table = self._get_column_table()
        column = table._meta.get_field(self.column_selected)
        return column

    def _get_column_table(self) -> DatabaseTable:
        # start with our base table and follow relations to current one
        table = self._get_base_table()  # will change each loop below
        for parent in self.column_parents:
            column = table._meta.get_field(parent)
            table = column.related_model
        return table

    def _set_column_options(self):
        table = self._get_column_table()

        # columns = table.get_column_names()  # doesn't work for non-simmate models (User)
        # so we copy that code here (consider a util)
        columns = [
            column.name
            for column in table._meta.get_fields()
            if not column.many_to_many and not column.one_to_many
            # TODO: and column not in table.exclude_from_api
        ]
        # TODO: check filter_methods -- maybe have as a separate section...?

        # populate col fields
        columns.sort()  # to make alphabetical
        self.column_options = [(c, c) for c in columns]  # options must be tuple
        self.column_options_hash = hash_options(self.column_options)

        # reset downstream options
        self.column_selected = None
        self.reset_metric()
        self.call("refresh_select2")

    def set_column_selected(self, column_selected):

        self.column_selected = column_selected

        column_type = self._get_column_type()

        if column_type in [table_column.DateField, table_column.DateTimeField]:
            pass  # TODO

        # If we have a relation, the user must select a column on the related table.
        # Note, we removed and *_to_many relations in _set_column_options
        elif column_type in [
            table_column.ForeignKey,
            table_column.OneToOneField,
            table_column.OneToOneRel,  # reverse for OneToOneField
        ]:
            self.column_parents.append(self.column_selected)
            self._set_column_options()

        # If we have a column, we can move on to selecting the metric
        else:
            metric_options = list(
                FilteredScope.lookup_type_defaults[column_type].keys()
            )

            self.metric_selected = None
            self.metric_options = [
                (key, FilteredScope.field_lookups_config[key]) for key in metric_options
            ]
            self.metric_options_hash = hash_options(self.metric_options)

        self.reset_filter_value()
        self.call("refresh_select2")

    def _reset_column_selection(self):
        self.column_selected = None
        self.column_parents = []
        self.column_options = []
        self.column_options_hash = None
        self._set_column_options()

    # -------------------------------------------------------------------------

    metric_selected = None
    metric_options = []
    metric_options_hash = None

    def set_metric_selected(self, metric_selected):
        self.metric_selected = metric_selected

        self.reset_filter_value()

        column_type = self._get_column_type()
        self.filter_value_type = FilteredScope.lookup_type_defaults[column_type][
            self.metric_selected
        ]

    def reset_metric(self):
        self.metric_selected = None
        self.metric_options = []
        self.metric_options_hash = None
        self.reset_filter_value()

    # -------------------------------------------------------------------------

    # Filter Value(s)

    filter_value = None  # data type depends on value_type
    filter_value_type = None  # e.g. "number" or "text"

    def reset_filter_value(self):
        self.filter_value = None
        self.filter_value_type = None

    # -------------------------------------------------------------------------

    filters = []

    def reset_new_filter(self):  # just an alias
        self._reset_column_selection()  # will cascade through metric/filter_value

    def add_new_filter(self):

        column_name = (
            "__".join(self.column_parents) + "__" + self.column_selected
            if self.column_parents
            else self.column_selected
        )

        metric = self.metric_selected

        # Convert value to proper python data type(s)
        value = self.filter_value
        vtype = self.filter_value_type
        if vtype == "number":
            filter_value = float(value) if "." in value else int(value)

        elif vtype in ["number-range", "number-list"]:
            filter_value = [float(v) if "." in v else int(v) for v in value.split(",")]

        elif vtype == "text":
            filter_value = str(value)

        elif vtype == "text-list":
            # BUG: we assume all of these are numeric for now
            filter_value = [float(v) if "." in v else int(v) for v in value.split(",")]

        elif vtype == "checkbox-isnull":
            filter_value = self.filter_value

        elif vtype == "checkbox-bool":
            filter_value = self.filter_value

        else:
            raise Exception(f"Unknown filter value type {self.filter_value_type}")

        new_filter = {
            "column_name": column_name,
            "metric": metric,
            "metric_display": FilteredScope.field_lookups_config[metric],
            "value": filter_value,
        }
        self.filters.append(new_filter)

        self.reset_new_filter()

    def remove_filter(self, remove_idx):
        self.filters.pop(remove_idx)

    def _load_filters(self, filters: dict):
        for entry, filter_value in filters.items():
            sections = entry.split("__")

            if len(sections) == 1:
                column_name = sections[0]
                metric = "exact"
            elif sections[-1] in FilteredScope.field_lookups_config.keys():
                column_name = "__".join(sections[:-1])
                metric = sections[-1]
            else:
                column_name = "__".join(sections)
                metric = "exact"

            new_filter = {
                "column_name": column_name,
                "metric": metric,
                "metric_display": FilteredScope.field_lookups_config[metric],
                "value": filter_value,
            }
            self.filters.append(new_filter)

    def apply_filters(self):  # send to a new URL

        filters_new = {}
        for entry in self.filters:
            key = entry["column_name"]
            if entry["metric"] != "exact":
                key += "__" + entry["metric"]
            filters_new[key] = entry["value"]
        url_get_clause = "?" + "&".join([f"{k}={v}" for k, v in filters_new.items()])

        # Note: page number, page size, limit, etc. are reset on a new filter query

        final_url = self.parent_url + url_get_clause
        return redirect(final_url)

    # -------------------------------------------------------------------------


def hash_options(options: list[tuple]) -> str:
    # for speed, we only hash the keys, which are shorter and should be
    # consistent with all their values anyways
    return str(hash(";".join([str(k) for k, _ in options])))
