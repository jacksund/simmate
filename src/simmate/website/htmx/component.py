# -*- coding: utf-8 -*-

import re
from typing import get_args, get_origin

from django.forms import Form as DjangoForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from simmate.utilities import dotdict, str_to_datatype

from .utilities import get_uuid_starting_with_letter, htmx_redirect

# for cachetools v1 and v2 support
try:
    from cachetools.lru import LRUCache
except ImportError:
    from cachetools import LRUCache

LOCAL_COMPONENT_CACHE = LRUCache(maxsize=10_000)


class HtmxComponent:

    component_id = None

    post_data = None

    def __init__(self, context: dict = None, **kwargs):
        # Objects are always initialized through the {% htmx_component ... %} templatetag.
        # So they are built when the html page is being rendered. On init, we
        # also add it to the cache, so that htmx ajax calls can load the object
        # from cache using the component_id
        self.component_id = get_uuid_starting_with_letter()
        self.intial_context = context
        self.update_caches()
        # self.mount()

    @classmethod
    @property
    def component_name(cls) -> str:
        # adds a hyphen between each capital letter (ExampleName --> example-name)
        # copied from https://stackoverflow.com/questions/199059/
        return re.sub(r"(\w)([A-Z])", r"\1-\2", cls.__name__).lower()

    # @classmethod
    # @property
    # def template_name(self) -> str:
    #     """
    #     Sets a default template name based on component's name
    #     """
    #     # Convert component name with a dot to a folder structure
    #     template_name = self.component_name.replace(".", "/")
    #     self.template_name = f"htmx/{template_name}.html"

    # -------------------------------------------------------------------------

    @classmethod
    def from_cache(cls, component_id: str) -> "HtmxComponent":

        component_cache_key = f"htmx:component:{component_id}"

        # try local cache
        cached_component = cls.from_local_cache(component_cache_key)
        if cached_component:
            return cached_component
        else:
            raise Exception()

        # try django cache  (DISABLED FOR NOW)
        # cached_component = cls.from_django_cache(component_cache_key)
        # if cached_component:
        #     return cached_component

    @staticmethod
    def from_local_cache(component_cache_key: str) -> "HtmxComponent":
        return LOCAL_COMPONENT_CACHE.get(component_cache_key)

    # -------------------------------------------------------------------------

    @property
    def component_cache_key(self):
        return f"htmx:component:{self.component_id}"

    def update_caches(self):
        self.to_local_cache()
        # self.to_django_cache()  # DISABLE FOR NOW

    def to_local_cache(self):
        LOCAL_COMPONENT_CACHE[self.component_cache_key] = self

    # def to_django_cache(self):
    #     cache_full_tree(self)

    # -------------------------------------------------------------------------

    _direct_obj_attrs_in_context: bool = False

    def get_context(self):
        obj_attrs = self.__dict__ if self._direct_obj_attrs_in_context else {}
        return {
            "component": self,
            **obj_attrs,
        }
        # **self.initial_context.flatten(),  # include this?

    def handle_request(self, request) -> HttpResponse:
        self.post_data = self.parse_post_data(request)
        # TODO: process
        return render(
            request,
            self.template_name,
            self.get_context(),
        )

    # -------------------------------------------------------------------------

    ####
    # request.POST data parsing + cleaning
    ####

    post_data_form: DjangoForm = None
    post_data_mappings: dict = {}

    def parse_post_data(self, request):

        # TODO: allow other more robust parsing methods. For example:
        #   1. simmate.utilities.str_to_datatype --> uses a mapping dict for type
        #   2. a pydantic class
        #   3. django form class

        # BUG:
        # For now, I don't want the boilerplate associated with those methods,
        # so I naively try parsing to the correct format. This can lead to bugs
        # though -- such as someone typing "false" into a text field and it
        # incorrectly being converted to a boolean when it should stay as a str.
        # As another example, we might have a multiselect with one or zero items
        # selected. This default parser would incorrectly convert to None or
        # a single type, rather than [] or ["example"]

        result = {}
        # note: all values are given as a list for requst.POST
        for key, values in request.POST.lists():

            target_type = self.post_data_mappings.get(key, None)

            # if it isn't explicitly given as a list type AND it has only 0 or 1
            # entries in the list, then we assume it should not be a list.
            if get_origin(target_type) != list and len(values) == 1:
                result[key] = str_to_datatype(
                    key,
                    values[0],
                    {key: target_type},
                    allow_type_guessing=True,
                )
            else:
                # we have a list and it must be one of...
                # list[bool], list[str], list[float], list[int]
                # grab inner type (e.g. list[str] -> str)
                target_subtype = get_args(target_type)[-1] if target_type else None
                result[key] = [
                    str_to_datatype(
                        key,
                        value,
                        {key: target_subtype},
                        allow_type_guessing=True,
                    )
                    for value in values
                ]

        return dotdict(result)

    # -------------------------------------------------------------------------

    template_name: str = "htmx/example_form.html"

    status_options = [
        (o, o)
        for o in [
            "option one",
            "option two",
            "option three",
        ]
    ]

    def run_some_js(self, request) -> JsonResponse:
        actions = [
            {"showAlert": ["Hello from Django!"]},
            {"highlight": ["#result"]},
        ]
        return JsonResponse(actions, safe=False)

    def add_molecule_image(self, request):
        from simmate.toolkit import Molecule

        self.actions = [
            {
                "add_mol_viewer": [
                    "jacks-molecule",
                    Molecule.from_smiles("CCCCCC").to_sdf(),
                    200,
                    300,
                ]
            }
        ]
        return self.handle_request(request)

    def update_selection_test(self, request):
        self.new_selection = True
        self.actions = [
            {"refresh_select2": []},
        ]
        return self.handle_request(request)
