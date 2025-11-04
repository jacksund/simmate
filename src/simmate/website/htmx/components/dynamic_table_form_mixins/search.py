# -*- coding: utf-8 -*-

import json
import urllib

from django.shortcuts import redirect


class SearchMixin:

    # for form_mode "search"

    general_search_inputs = [
        "id__in",
        "page_size",
        "order_by",
        "reverse_order_by",
    ]

    page_size_options = [
        25,
        50,
        100,
    ]

    @property
    def order_by_options(self):
        return self.table.get_column_names(include_relations=False)

    def mount_for_search(self):
        return  # default is there's nothing extra to do

    def to_search_dict(self, **kwargs) -> dict:
        return self._get_default_search_dict(**kwargs)

    def _get_default_search_dict(self, include_empties: bool = False):
        # kept as a separate method so others can call it in a clean manner
        # and avoid any super() stuff

        # build the dict of API filters
        config = {}
        for search_key in list(self.form_data.keys()) + self.general_search_inputs:
            search_val = self.form_data.get(search_key, None)
            if not include_empties and search_val in [None, "", []]:
                continue
            if search_key.endswith("_ids"):  # assume m2m and we want __in query
                # ex: config["tags__id__in"] = [1,2,3,...]
                # BUG: need to standardize this
                config[f"{search_key[:-4]}s__id__in"] = search_val
            else:
                config[search_key] = search_val

        # -----------------
        # Modify special cases for filters

        # comments should be a contains search
        if "comments" in config.keys():
            config["comments__contains"] = config.pop("comments")

        # reformat __in to python list
        if "id__in" in config.keys():
            # BUG: check to see it was input correctly?
            input_value = config["id__in"]
            if isinstance(input_value, int):
                config["id__in"] = [input_value]  # it is a single id lookup
            else:
                config["id__in"] = [int(i) for i in input_value.split(",")]

        if "order_by" in config.keys() and config.pop("reverse_order_by", False):
            config["order_by"] = "-" + config["order_by"]

        # TODO: should prob be in mol mixin
        # moleculequery's key depends on its type
        if "molecule" in config.keys():
            config[self.molecule_query_type] = self._molecule_obj.to_smiles()
            config.pop("molecule")

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
