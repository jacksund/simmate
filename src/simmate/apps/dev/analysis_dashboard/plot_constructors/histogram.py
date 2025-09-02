# -*- coding: utf-8 -*-

import pandas as pd
import plotly.express as px
import streamlit as st

from .base import PlotConstructor


class Histogram(PlotConstructor):

    display_name = "Histogram"
    required_inputs = ["x"]

    @staticmethod
    def get_inputs(df: pd.DataFrame) -> dict:
        return {
            "x": st.selectbox(
                label="X",
                index=None,
                options=df.columns,
            ),
            "histfunc": st.selectbox(
                label="Aggregation Function",
                index=0,
                options=[
                    "count",
                    "sum",
                    "avg",
                    "min",
                    "max",
                ],
            ),
            "y": st.selectbox(
                label="Y (passed to Aggregation Function)",
                index=None,
                options=df.columns,
            ),
            "cumulative": st.checkbox(
                label="Cumulative Aggregation",
                value=False,
            ),
            "nbins": st.number_input(
                label="Number of Bins",
                min_value=0,
                value=None,
            ),
            "color": st.selectbox(
                label="Color",
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
    def get_plot(cls, df: pd.DataFrame, plot_config: dict):

        fig = px.histogram(
            data_frame=df,
            **plot_config,
        )

        fig.update_layout(dragmode="zoom")

        return fig
