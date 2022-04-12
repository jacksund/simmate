# -*- coding: utf-8 -*-

from textwrap import dedent

from django import template
from django.utils.safestring import mark_safe

from pdoc.render_helpers import to_html


# We need a registration instance in order to configure everything with Django
register = template.Library()


@register.filter(name="markdown")
def markdown_to_html(markdown_str):
    """
    Converts markdown to rendered HTML using utilities from pdoc. This is especially
    useful for rendering python docstrings.
    """

    # Docstrings often have the entire string indented a number of times.
    # We need to strip those idents away to render properly
    markdown_cleaned = dedent(markdown_str)

    final_html = to_html(markdown_cleaned)

    # Because we added new html to our script, we need to have Django check it
    # ensure it safe before returning. Read more about this here:
    # https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#filters-and-auto-escaping
    return mark_safe(final_html)
