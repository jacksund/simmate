# -*- coding: utf-8 -*-

import re
from pathlib import Path


class Figure:
    method_type: str = "objectmethod"  # or "classmethod"

    @classmethod
    @property
    def name(cls):
        # https://stackoverflow.com/questions/1175208/
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name

    @staticmethod
    def get_plot(parent_class):
        raise NotImplementedError("Please implement a get_plot method for your figure")

    @classmethod
    def register_to_class(cls, parent_class):
        cls.parent = parent_class

        # TODO: consider making a decorator so I don't have to write out each
        # of these functions
        def get_plot(input_obj=None, **kwargs):
            plot = cls.get_plot(input_obj, **kwargs)
            return plot

        def view_plot(input_obj=None, **kwargs):
            return cls.view_plot(input_obj, **kwargs)

        def write_plot(input_obj=None, **kwargs):
            return cls.write_plot(input_obj, **kwargs)

        def get_html_div(input_obj=None, **kwargs):
            return cls.get_html_div(input_obj, **kwargs)

        # OPTIMIZE: is there better way to determine method type?
        # # https://stackoverflow.com/questions/19227724/
        # import inspect
        # if inspect.ismethod(cls.method) and cls.method.__self__ is cls:
        #     # method bound to the class, e.g. a classmethod

        if cls.method_type == "classmethod":
            setattr(
                parent_class,
                f"get_{cls.name}_plot",
                classmethod(get_plot),
            )
            setattr(
                parent_class,
                f"view_{cls.name}_plot",
                classmethod(view_plot),
            )
            setattr(
                parent_class,
                f"write_{cls.name}_plot",
                classmethod(write_plot),
            )
            setattr(
                parent_class,
                f"get_{cls.name}_html_div",
                classmethod(get_html_div),
            )
        elif cls.method_type == "objectmethod":
            setattr(
                parent_class,
                f"get_{cls.name}_plot",
                get_plot,
            )
            setattr(
                parent_class,
                f"view_{cls.name}_plot",
                view_plot,
            )
            setattr(
                parent_class,
                f"write_{cls.name}_plot",
                write_plot,
            )
            setattr(
                parent_class,
                f"get_{cls.name}_html_div",
                get_html_div,
            )

    @classmethod
    def view_plot(cls, parent_class, **kwargs):
        raise NotImplementedError(
            "Please implement a view_plot method for your figure or inherit from "
            "common figure types (e.g. a PlotlyFigure)"
        )

    @classmethod
    def write_plot(cls, directory: Path, **kwargs):
        raise NotImplementedError(
            "Please implement a write_plot method for your figure or inherit from "
            "common figure types (e.g. a PlotlyFigure)"
        )

    @classmethod
    def get_html_div(cls, **kwargs):
        raise NotImplementedError(
            "Please implement a get_html_div method for your figure or inherit from "
            "common figure types (e.g. a PlotlyFigure)"
        )
