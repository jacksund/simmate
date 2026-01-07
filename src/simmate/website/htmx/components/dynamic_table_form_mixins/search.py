# -*- coding: utf-8 -*-

import json
import re
import urllib

from django.shortcuts import redirect


class SearchMixin:

    # for form_mode "search"

    ignore_on_search: list[str] = []
    """
    List of columns/fields to ignore when the form_mode = "search"
    """

    page_size_options = [
        25,
        50,
        100,
    ]

    @property
    def order_by_options(self):
        return self.table.get_column_names(include_to_one_relations=False)

    def mount_for_search(self):
        return  # default is there's nothing extra to do

    def to_search_dict(self, include_empties: bool = False) -> dict:
        # The default is just to remove all empty values
        config = {}
        for search_key, search_value in self.form_data.items():
            if search_value in [None, "", []] or search_key in self.ignore_on_search:
                continue
            config[search_key] = search_value
        return config

    def check_form_for_search(self):
        return  # nothing to check

    def unmount_for_search(self):
        return  # default is there's nothing extra to do

    def save_to_db_for_search(self):
        pass  # nothing to save

    def get_search_redirect(self):

        # moleclue_query: str
        # self.set_molecule(moleclue_query, render=False)

        # grab all metadata filters and convert to url GET params
        filters = self.to_search_dict()

        # convert all values to json serialized strings
        filters_serialized = {k: json.dumps(v) for k, v in filters.items()}

        # encode any special characters for the url
        url_get_clause = urllib.parse.urlencode(filters_serialized)

        final_url = self.parent_url + "?" + url_get_clause
        return redirect(final_url)

    # -------------------------------------------------------------------------

    def on_change_hook__id__in(self):
        input_value = self.form_data["id__in"]
        if isinstance(input_value, int):
            self.form_data["id__in"] = [input_value]  # it is a single id lookup
        else:
            self.form_data["id__in"] = [
                int(i) for i in re.split(",| |\n", input_value) if i
            ]

    def on_change_hook__reverse_order_by(self):
        # by popping it, we ensure this hook is called EVERY htmx call
        reverse = self.form_data.pop("reverse_order_by", False)
        order_col = self.form_data.get("order_by")
        if order_col:
            order_col = order_col.strip("-")
            if reverse:
                order_col = "-" + order_col
        self.form_data["order_by"] = order_col
