# -*- coding: utf-8 -*-

import re
from typing import get_args, get_origin

from django.http import HttpRequest, HttpResponse, JsonResponse
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

    component_id: str = None

    post_data: dict = None

    form_data: dict = None

    js_actions: list[dict] = None

    inital_context: dict = None

    request: HttpRequest = None  # overwritten on each new ajax call

    def __init__(self, context: dict = None, **kwargs):
        # Objects are always initialized through the {% htmx_component ... %} templatetag.
        # So they are built when the html page is being rendered. On init, we
        # also add it to the cache, so that htmx ajax calls can load the object
        # from cache using the component_id
        self.component_id = get_uuid_starting_with_letter()
        self.form_data = {}
        self.intial_context = context
        self.request = context.request
        self.update_caches()
        self.mount()

    # -------------------------------------------------------------------------

    _direct_obj_attrs_in_context: bool = False

    def get_context(self):
        obj_attrs = self.__dict__ if self._direct_obj_attrs_in_context else {}
        return {
            "component": self,
            **obj_attrs,
        }
        # **self.initial_context.flatten(),  # include this?

    def handle_request(self, request, method_name: str = None) -> HttpResponse:

        self.request = request  # for easy access elsewhere

        self.js_actions = []  # reset as to not repeat last request's actions

        self.pre_parse()
        self.post_data = self.parse_post_data()
        self.post_parse()

        self.form_data.update(self.post_data)

        if method_name:
            method = getattr(self, method_name)
            response = method()
        else:
            response = self.process()

        # response is typically None, meaning we defer to rendering the component
        # template again.
        # But in some cases, it can return a JsonResponse, a URL, or some html
        # that takes priority
        if isinstance(response, JsonResponse):
            return response
        elif False and isinstance(response, str):  # DISABLED -- need better check
            return htmx_redirect(response)  # redirect to url
        elif response is not None:
            return response  # could be Http, html or something else
        else:
            render(
                request,
                self.template_name,
                self.get_context(),
            )

    # -------------------------------------------------------------------------

    # LOADING FROM CACHE METHODS

    @classmethod
    def from_cache(cls, component_id: str) -> "HtmxComponent":

        component_cache_key = f"htmx:component:{component_id}"

        # try local cache
        cached_component = cls.from_local_cache(component_cache_key)
        if cached_component:
            return cached_component
        else:
            raise Exception("Failed to load component from cache")

        # try django cache  (DISABLED FOR NOW)
        # cached_component = cls.from_django_cache(component_cache_key)
        # if cached_component:
        #     return cached_component

    @staticmethod
    def from_local_cache(component_cache_key: str) -> "HtmxComponent":
        return LOCAL_COMPONENT_CACHE.get(component_cache_key)

    # @staticmethod
    # def from_django_cache(self):
    #     ....from_dict(...)

    # -------------------------------------------------------------------------

    # ADDING TO CACHE METHODS

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

    # request.POST data parsing + cleaning

    post_data_mappings: dict = {}

    def parse_post_data(self):

        # TODO: allow other more robust parsing methods. For example:
        #   1. a pydantic class
        #   2. django form class

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
        for key, values in self.request.POST.lists():

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

    # HOOKS -- all do nothing by default

    def mount(self):  # aka on_init() or on_create()
        pass

    def pre_parse(self):
        pass

    def post_parse(self):
        pass

    def process(self):
        pass

    # -------------------------------------------------------------------------
