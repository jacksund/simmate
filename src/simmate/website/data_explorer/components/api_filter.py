from django_unicorn.components import UnicornView

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, FilteredScope, table_column

# TODO: move to util and combine with var used in views.py
ALL_API_TABLES = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for table_name in settings.website.data
}


class ApiFilterView(UnicornView):

    template_name = "data_explorer_dev/api_filter.html"

    # class Meta:
    #     javascript_exclude = (
    #         "page_title",
    #         "breadcrumbs",
    #         "breadcrumb_active",
    #         "user_options",
    #         "status_options",
    #         "required_fields",
    #     )

    # -------------------------------------------------------------------------

    # table = None

    def mount(self):
        self.table = self._determine_table()
        url_config = self.table._parse_request_get(self.request)

        self.filters = [f for f in url_config["filters"].items()]
        self._set_column_options()

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

    # @property
    # def _table(self):
    #     return ALL_API_TABLES[self.table_name]

    # -------------------------------------------------------------------------

    # column_table --> current table we are looking at (e.g. could be User for compound__user)
    column_selected = None
    column_parents = []
    column_options = []
    column_options_hash = None

    def _set_column_options(self, table=None):
        if not table:
            table = self.table
        # columns = table.get_column_names()  # doesn't work for non-simmate models (User)
        # So we copy that code here (consider a util)
        columns = [column.name for column in table._meta.get_fields()]
        columns.sort()  # to make alphabetical
        self.column_options = [(c, c) for c in columns]  # options must be tuple
        self.column_options_hash = hash_options(self.column_options)

    def set_column_selected(self, column_selected):

        self.column_selected = column_selected

        column = self.table._meta.get_field(self.column_selected)
        column_type = type(column)
        if column_type in [
            table_column.ForeignKey,
            table_column.ManyToManyField,
            table_column.OneToOneField,
        ]:
            self.column_parents.append(self.column_selected)
            self.column_selected = None
            self._set_column_options(column.related_model)
            self.call("refresh_select2")
            return

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
