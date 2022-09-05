# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.visualization.plotting import Figure


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
