from django_unicorn.components import UnicornView

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable

# TODO: move to util and combine with var used in views.py
ALL_API_TABLES = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for table_name in settings.website.data
}


class ApiFilterView(UnicornView):

    template_name = "data_explorer_dev/api_filter.html"

    task = ""
    tasks = []

    def mount(self):
        table = self._determine_table()
        url_config = table._parse_request_get(self.request)
        self.tasks = [f for f in url_config["filters"].items()]

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

    def add(self):
        self.tasks.append(self.task)
        self.task = ""
