# -*- coding: utf-8 -*-

import pandas as pd
import plotly.express as px
import streamlit as st

from .base import PlotConstructor


class ScatterMatrix(PlotConstructor):

    display_name = "Scatter Matrix"
    required_inputs = ["dimensions"]

    @staticmethod
    def get_inputs(df: pd.DataFrame):
        return {
            "dimensions": st.multiselect(
                label="Dimensions",
                options=df.columns,
                default=[],
            ),
            "color": st.selectbox(
                label="Color",
                index=None,
                options=df.columns,
            ),
            "size": st.selectbox(
                label="Size",
                index=None,
                options=df.columns,
            ),
            "symbol": st.selectbox(
                label="Symbol",
                index=None,
                options=df.columns,
            ),
            "opacity": st.slider(
                label="Opacity",
                min_value=0.0,
                max_value=1.0,
                value=1.0,
            ),
        }

    @classmethod
    def check_inputs(cls, df: pd.DataFrame, plot_config: dict) -> bool:

        # ensure required inputs
        for key in cls.required_inputs:
            if plot_config[key] is None:
                return False

        # There should be more than 1 dimension
        if len(plot_config["dimensions"]) < 2:
            return False

        return True

    @staticmethod
    def get_plot(df: pd.DataFrame, plot_config: dict):
        fig = px.scatter_matrix(
            data_frame=df,
            **plot_config,
            # custom_data=smiles_column,  # required for drawing mols on hover
        )
        fig.update_traces(diagonal_visible=False)
        fig.update_layout(dragmode="zoom")
        return fig
