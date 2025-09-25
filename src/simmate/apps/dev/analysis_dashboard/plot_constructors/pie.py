# -*- coding: utf-8 -*-

import pandas as pd
import plotly.express as px
import streamlit as st

from .base import PlotConstructor


class Pie(PlotConstructor):

    display_name = "Pie"
    required_inputs = ["names", "values"]

    @staticmethod
    def get_inputs(df: pd.DataFrame) -> dict:
        return {
            "names": st.selectbox(
                label="Section Names",
                index=None,
                options=df.columns,
            ),
            "values": st.selectbox(
                label="Section Values",
                index=None,
                options=df.columns,
            ),
            "color": st.selectbox(
                label="Color",
                index=None,
                options=df.columns,
            ),
        }

    @classmethod
    def get_plot(cls, df: pd.DataFrame, plot_config: dict):

        fig = px.pie(
            data_frame=df,
            **plot_config,
        )

        fig.update_layout(dragmode="zoom")

        return fig
