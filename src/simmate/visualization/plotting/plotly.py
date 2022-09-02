# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.visualization.plotting import Figure


class PlotlyFigure(Figure):
    @classmethod
    def view_plot(cls, parent_class, **kwargs):
        figure = cls.get_plot(parent_class, **kwargs)
        figure.show(renderer="browser")

    @classmethod
    def write_plot(cls, parent_class, directory: Path = None, **kwargs):
        if not directory:
            directory = Path.cwd()
        figure = cls.get_plot(parent_class, **kwargs)
        figure.write_html(
            directory / f"{cls.name}.html",
            include_plotlyjs="cdn",
        )

    @classmethod
    def get_html_div(cls, parent_class, **kwargs):
        raise NotImplementedError(
            "Matplotlib figures cannot make a standalone html div."
        )
