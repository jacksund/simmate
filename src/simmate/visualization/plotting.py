# -*- coding: utf-8 -*-

import re

from pathlib import Path


class PlotlyFigure:
    @classmethod
    @property
    def method_name(cls):
        # https://stackoverflow.com/questions/1175208/
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name

    @classmethod
    def get_plot(cls):
        raise NotImplementedError()

    @classmethod
    def view_plot(cls):
        figure = cls.get_plot()
        figure.show(renderer="browser")

    @classmethod
    def write_plot(cls, directory: Path):
        figure = cls.get_plot()
        figure.write_html(
            directory / f"{cls.method_name}.html",
            include_plotlyjs="cdn",
        )

    @classmethod
    def register_to_class(cls, parent_class):

        setattr(parent_class, f"get_{cls.method_name}", cls.get_plot)
        setattr(parent_class, f"view_{cls.method_name}", cls.view_plot)
        setattr(parent_class, f"write_{cls.method_name}", cls.write_plot)
