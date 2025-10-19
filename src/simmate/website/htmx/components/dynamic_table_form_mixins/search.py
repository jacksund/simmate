# -*- coding: utf-8 -*-

import json
import urllib

from django.shortcuts import redirect


class SearchMixin:

    # for form_mode "search"

    search_inputs = [
        "id__in",
        "page_size",
        "order_by",
        # "reverse_order_by",
    ]

    # assumed filters from DatabaseTable
    id__in = None

    page_size = None
    page_size_options = [
        25,
        50,
        100,
    ]

    order_by = None
    reverse_order_by = False

    @property
    def order_by_options(self):
        # reformat into tuple of (value, display)
        return [(col, col) for col in self.table.get_column_names()]

    def set_order_by(self, value):
        if value.startswith("-"):
            self.order_by = value[1:]
            self.reverse_order_by = True
        else:
            self.order_by = value
            self.reverse_order_by = False

    def to_search_dict(self, **kwargs) -> dict:
        return self._get_default_search_dict(**kwargs)

    def _get_default_search_dict(self, include_empties: bool = False):
        # !!! consider merging functionality with _get_default_db_dict
        config = {}
        for form_attr in self.search_inputs:
            current_val = getattr(self, form_attr)
            current_val = parse_value(current_val)
            if not include_empties and current_val is None:
                continue
            config[form_attr] = current_val

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
        if "order_by" in config.keys() and self.reverse_order_by:
            config["order_by"] = "-" + config["order_by"]

        # TODO: should prob be in mol mixin
        # moleculequery's key depends on its type
        if "molecule" in config.keys():
            config[self.molecule_query_type] = self._molecule_obj.to_smiles()
            config.pop("molecule")

        # TODO: support other m2m
        if hasattr(self, "tag_ids") and self.tag_ids:
            config["tags__id__in"] = self.tag_ids

        return config

    def get_search_redirect(self):  # *args, **kwargs

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

    def mount_for_search(self):
        raise NotImplementedError("mount_for_update")
        return  # default is there's nothing extra to do

    def unmount_for_search(self):
        return  # default is there's nothing extra to do

    def save_to_db_for_search(self):
        pass  # nothing to save
