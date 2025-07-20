# -*- coding: utf-8 -*-

import re

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

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
        # Switch from class name to unicorn convent (ExampleNameView --> example-name)
        # adds a hyphen between each capital letter
        # copied from https://stackoverflow.com/questions/199059/
        return re.sub(r"(\w)([A-Z])", r"\1-\2", cls.__name__).lower()

    template_name: str = "htmx/example_form.html"
    # @classmethod
    # @property
    # def template_name(self) -> str:
    #     """
    #     Sets a default template name based on component's name if necessary.
    #     """
    #     # Convert component name with a dot to a folder structure
    #     template_name = self.component_name.replace(".", "/")
    #     self.template_name = f"unicorn/{template_name}.html"

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
        self.post_data = request.POST
        # TODO: process
        return render(
            request,
            self.template_name,
            self.get_context(),
        )

    # -------------------------------------------------------------------------

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
        print(request.POST)
        self.new_selection = True
        self.actions = [
            {"refresh_select2": []},
        ]
        return self.handle_request(request)
