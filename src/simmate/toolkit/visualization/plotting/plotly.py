# -*- coding: utf-8 -*-

from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

from simmate.toolkit.visualization.plotting import Figure

pio.templates["simmate"] = go.layout.Template(
    layout=dict(
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            color="grey",
            size=12,
        ),
        colorway=[
            "rgba(16, 196, 105, 1)",  # green
            "rgba(4, 144, 204, 1)",  # blue
            "rgba(249, 200, 81, 1)",  # yellow
            "rgba(0, 0, 0, 1)",  # black
            "rgba(255, 91, 91, 1)",  # red
            "rgba(143, 205, 255, 1)",  # light blue
            "rgba(200, 200, 200, 1)",  # light grey
            "rgba(100, 100, 100, 1)",  # dark grey
        ],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
        ),
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
)

# Compose with the default 'plotly' template
pio.templates.default = "plotly+simmate"


class PlotlyFigure(Figure):
    @classmethod
    def view_plot(cls, parent_class, **kwargs):
        figure = cls.get_plot(parent_class, **kwargs)
        cls.apply_theme(figure)
        figure.show(renderer="browser")

    @classmethod
    def write_plot(cls, parent_class, directory: Path = None, **kwargs):
        if not directory:
            directory = Path.cwd()
        figure = cls.get_plot(parent_class, **kwargs)
        cls.apply_theme(figure)
        figure.write_html(
            directory / f"{cls.name}.html",
            include_plotlyjs="cdn",
        )

    @classmethod
    def get_html_div(cls, parent_class, **kwargs):
        # Make the convergence figure and convert it to an html div
        figure = cls.get_plot(parent_class, **kwargs)
        cls.apply_theme(figure)
        html_div = figure.to_html(
            full_html=False,
            include_plotlyjs=False,
        )
        return html_div

    @staticmethod
    def apply_theme(plot):
        plot.update_layout(template="ggplot2")
