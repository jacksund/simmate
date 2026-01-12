# -*- coding: utf-8 -*-

import urllib
from textwrap import dedent

import markdown as MarkdownConverter
from django import template
from django.utils.safestring import mark_safe
from plotly.graph_objects import Figure

from simmate.database.base_data_types import Structure as DatabaseStructure
from simmate.toolkit import Structure as ToolkitStructure

register = template.Library()


@register.filter
def getattribute(obj, attr):
    """
    Wraps the getattr python method into a django template tag so that we
    can dynamically grab object properties.

    Example use:
    ``` html
    {{ my_object|getattribute:example_var }}
    ```

    Note `example_var` in the example above is a string set to a property name.
    """
    try:
        return getattr(obj, attr)
    except:  # RelatedObjectDoesNotExist
        return None


@register.filter
def getitem(dictionary, key):
    """
    Wraps the get dictionary python method into a django template tag so that we
    can dynamically grab items.

    Example use:
    ``` html
    {{ my_dict|getitem:example_key }}
    ```
    """
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def update_url(context, **kwargs):
    """
    Returns the current URL with updated GET parameters.

    Example use:
    ``` html
    <a href="{% update_url page=2 sort='name' %}">Next Page</a>
    ```
    """
    request = context["request"]
    get_params = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == "":
            get_params.pop(k, None)
        else:
            get_params[k] = v
    query = get_params.urlencode()
    return f"?{query}"


@register.filter(name="markdown")
def markdown_to_html(markdown_str):
    """
    Converts markdown to rendered HTML. This is especially
    useful for rendering python docstrings.
    """

    # Docstrings often have the entire string indented a number of times.
    # We need to strip those idents away to render properly
    markdown_cleaned = dedent(markdown_str)

    final_html = MarkdownConverter.markdown(
        markdown_cleaned,
        # add exts for code syntax highlighting
        # followed guide from https://realpython.com/django-markdown/
        extensions=["fenced_code", "codehilite"],
    )

    # Because we added new html to our script, we need to have Django check it
    # ensure it safe before returning. Read more about this here:
    # https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#filters-and-auto-escaping
    return mark_safe(final_html)


@register.filter(name="chemical_formula")
def formula_to_html(formula_str):
    """
    Converts a chemical formula to html format by wrapping numbers with a
    subscript tag. For example, "Y2CF2" will be turned into "Y<sub>2</sub>CF<sub>2</sub>"
    so that it looks nice in a webpage
    """

    # start with an empty string that we build off of
    new_formula_str = ""

    for character in formula_str:
        # if it's a number or a decimal, we wrap it in <sub> tags
        if character.isnumeric() or character == ".":
            character = f"<sub>{character}</sub>"
        # now add it to our result
        new_formula_str += character

    # Because we added new html to our script, we need to have Django check it
    # ensure it safe before returning. Read more about this here:
    # https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#filters-and-auto-escaping
    return mark_safe(new_formula_str)


@register.filter
def sdfdoodle(obj):
    """
    Converts an sdf string to one that can be passed to the doodle_molecule fxn

    Example use:
    ``` html
    {{ my_object|sdfdoodle }}
    ```
    """
    return obj.replace("\n", "\\n")


@register.inclusion_tag(
    filename="core_components/chem_elements/draw_3d_structure.html",
    takes_context=True,
)
def structure_3d(
    context: dict,
    structure: ToolkitStructure | DatabaseStructure,
):
    """
    Converts a toolkit Structure into a rendered 3D viewport.

    This is done by serializing the structure lattice, sites, and bonds and then
    sending this info to the frontend JS to be built and rendered with Three.js
    """

    # if we are given a structure that is a database table instance, we simply
    # grab the structure string
    if isinstance(structure, DatabaseStructure):
        structure = structure.to_toolkit()
    elif isinstance(structure, ToolkitStructure):
        pass  # already good to go with toolkit
    else:
        raise Exception(f"Unknown structure type provided: {type(structure)}")

    return {"structure": structure, "structure_serialized": structure.to_threejs_json()}


@register.filter(name="plotly_figure")
def plotly_figure(figure: Figure):
    """
    Converts a plotly figure object to an html element for the frontend.
    """
    # if isinstance(figure, Figure):
    hmtl = figure.to_html(
        full_html=False,
        include_plotlyjs=False,
    )
    return mark_safe(hmtl)
