# -*- coding: utf-8 -*-

import pandas as pd
import plotly.express as px
import streamlit as st

from .base import PlotConstructor


class Line(PlotConstructor):

    display_name = "Line"
    required_inputs = ["x", "y"]

    @staticmethod
    def get_inputs(df: pd.DataFrame) -> dict:
        return {
            "x": st.selectbox(
                label="X axis",
                index=None,
                options=df.columns,
            ),
            "y": st.selectbox(
                label="Y axis",
                index=None,
                options=df.columns,
            ),
            "color": st.selectbox(
                label="Color",
                index=None,
                options=df.columns,
            ),
            "symbol": st.selectbox(
                label="Symbol",
                index=None,
                options=df.columns,
            ),
        }

    @classmethod
    def get_plot(cls, df: pd.DataFrame, plot_config: dict):

        fig = px.line(
            data_frame=df,
            **plot_config,
        )

        fig.update_layout(dragmode="zoom")

        return fig
