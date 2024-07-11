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

    # class Meta:
    #     javascript_exclude = (
    #         # "page_title",
    #         # "breadcrumbs",
    #         # "breadcrumb_active",
    #         # "user_options",
    #         # "table",
    #         # "column_table",
    #         # "required_fields",
    #     )

    def mount(self):
        # load table
        table = self._determine_table()
        self.table_name = table.table_name

        # load url args + starting filters
        url_config = table._parse_request_get(self.request)
        self.filters = [f for f in url_config["filters"].items()]

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

    def set_column_selected(self, column_selected):

        self.column_selected = column_selected

        column = self._get_column()
        column_type = type(column)

        # If we have a relation, the user must select a column on the related table
        if column_type in [
            table_column.ForeignKey,
            table_column.OneToOneField,
            table_column.OneToOneRel,  # reverse for OneToOneField
        ]:
            self.column_parents.append(self.column_selected)
            self._set_column_options()

        # If we have a column, we can move on to selecting the metric
        else:
            metric_options = FilteredScope.lookup_type_defaults.get(column_type, None)

            if not metric_options:
                raise Exception(f"No options for {column_type}")

            self.metric_selected = None
            self.metric_options = [
                (key, FilteredScope.field_lookups_config[key]) for key in metric_options
            ]
            self.metric_options_hash = hash_options(self.metric_options)

        self.call("refresh_select2")

    # -------------------------------------------------------------------------

    metric_selected = None
    metric_options = []
    metric_options_hash = None

    def set_metric_selected(self, metric_selected):
        self.metric_selected = metric_selected

    def reset_metric(self):
        self.metric_selected = None
        self.metric_options = []
        self.metric_options_hash = None

    # -------------------------------------------------------------------------

    # Value(s)

    value = None  # data type depends on value_type
    value_hint = None  # e.g. "1, 2, 3 (separate with commas)"
    value_type = None  # e.g. "number" or "text"

    # -------------------------------------------------------------------------

    filters = []

    def add(self):
        self.tasks.append(self.task)
        self.task = ""

    # -------------------------------------------------------------------------


def hash_options(options: list[tuple]) -> str:
    # for speed, we only hash the keys, which are shorter and should be
    # consistent with all their values anyways
    return str(hash(";".join([str(k) for k, _ in options])))
