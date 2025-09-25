# -*- coding: utf-8 -*-

import pandas as pd

# import plotly.express as px
# import streamlit as st


class PlotConstructor:
    """
    An abstract base class for dynamically creating Plotly figures using
    Streamlit inputs.
    """

    display_name: str = None
    """
    Name of the figure type. This is what is displayed in the UI
    """

    required_inputs: list[str] = []
    """
    List of required input parameters in order to generate a plot. The names
    of these parameters should be present in the keys given by `get_inputs`
    """

    @staticmethod
    def get_inputs(df: pd.DataFrame) -> dict:
        raise NotImplementedError("No inputs were given!")

    @classmethod
    def check_inputs(cls, df: pd.DataFrame, plot_config: dict) -> bool:
        # By default we just check that the required inputs are set, but in
        # other cases this methand can be overwritten
        for key in cls.required_inputs:
            if plot_config[key] is None:
                return False
        return True

    @staticmethod
    def get_plot(df: pd.DataFrame, plot_config: dict):  # returns plotly Figure obj
        raise NotImplementedError("No plot was given!")

    # -------------------------------------------------------------------------
    # Utils

    @staticmethod
    def _clean_inputs(df: pd.DataFrame, plot_config: dict):
        # special case: opacity will be given as a column name, but we need
        # to convert it to a float series on a scale from 0-1
        opacity_column = plot_config["opacity"]
        if opacity_column is not None:
            plot_config["opacity"] = (
                df[opacity_column] / df[opacity_column].max()
                if opacity_column
                else None
            )  # Normalizes to 0-1 scale
