# -*- coding: utf-8 -*-

import uuid

from django.http import HttpResponse


def htmx_redirect(url: str) -> HttpResponse:
    response = HttpResponse()
    response["HX-Redirect"] = url
    return response


def get_uuid_starting_with_letter() -> str:
    # because the id is also used as html element ids, it must start with
    # a letter. We just generate uuids until we get one like that
    while True:
        u = uuid.uuid4()
        if u.hex[0].isalpha():
            return str(u)


def style_dashboard_figure(figure):
    """
    Applies a transparent background, semi-transparent grid, and neutral font
    so that plotly figures work in both light and dark mode. Callers can
    further `update_layout` for size, margins, etc.
    """
    grid_color = "rgba(128,128,128,0.2)"
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#888888"),
        xaxis=dict(gridcolor=grid_color),
        yaxis=dict(gridcolor=grid_color),
    )
    return figure
