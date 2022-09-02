# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.visualization.plotting import Figure


class MatPlotLibFigure(Figure):
    @classmethod
    def view_plot(cls, parent_class, **kwargs):
        figure = cls.get_plot(**kwargs)
        figure.show()

    @classmethod
    def write_plot(cls, directory: Path, **kwargs):
        if not directory:
            directory = Path.cwd()
        figure = cls.get_plot(**kwargs)
        filename = directory / f"{cls.name}.html"
        figure.savefig(filename)

    @classmethod
    def get_html_div(cls, **kwargs):
        # Make the convergence figure and convert it to an html div
        figure = cls.get_plot(**kwargs)
        html_div = figure.to_html(
            full_html=False,
            include_plotlyjs=False,
        )
        return html_div
