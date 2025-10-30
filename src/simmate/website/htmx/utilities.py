# -*- coding: utf-8 -*-

import importlib
from inspect import getmembers, isclass

from django.utils.module_loading import import_string

from simmate.configuration import settings
from simmate.utilities import get_app_submodule

from .components import HtmxComponent


def get_all_components(
    apps_to_search: list[str] = settings.apps,
    as_dict: bool = False,
) -> list[HtmxComponent]:
    """
    Goes through a list of apps and grabs all component objects available.
    By default, this will grab all installed 'settings.apps'
    """

    # django must be configured for us to iterate the apps

    from simmate.database import connect

    app_components = []
    for app_name in apps_to_search:
        # check if there is a components module for this app and load it if so
        components_path = get_app_submodule(app_name, "components")
        if not components_path:
            continue  # skip to the next app
        app_components_module = importlib.import_module(components_path)

        # iterate through each available object in the components file and find
        # which ones are component objects.

        # If an __all__ value is set, then this will take priority when grabbing
        # components from the module
        if hasattr(app_components_module, "__all__"):
            for component_name in app_components_module.__all__:
                component = getattr(app_components_module, component_name)
                if component not in app_components:
                    app_components.append(component)

        # otherwise we load ALL class objects from the module -- assuming the
        # user properly limited these to just HtmxComponent objects.
        else:
            # a tuple is returned by getmembers so c[0] is the string name while
            # c[1] is the python class object.
            app_components += [
                c[1] for c in getmembers(app_components_module) if isclass(c[1])
            ]

    return (
        app_components
        if not as_dict
        else {flow.component_name: flow for flow in app_components}
    )


def get_component(component_name: str):  # -> subclass of HtmxComponent
    """
    Given a component name (e.g. "project-form") or a full import
    path of a component, this will load and return the corresponding
    component class.
    """

    # "." in the name indicates an import path
    if "." in component_name:
        component_class = import_string(component_name)

    # otherwise search all components and see if there is a *single* match
    else:
        all_components = get_all_components(as_dict=True)
        component_class = all_components.get(component_name, None)
        if not component_class:
            raise Exception(
                f"Unable to find component class with name '{component_name}'"
            )

    return component_class
