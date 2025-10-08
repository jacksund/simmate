# -*- coding: utf-8 -*-

import pandas as pd
import plotly.express as px
import streamlit as st

from .base import PlotConstructor


class Scatter(PlotConstructor):

    display_name = "Scatter"
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
    def get_plot(cls, df: pd.DataFrame, plot_config: dict):

        # Hover template will be an empty space
        # hovertemplate = "____________________________________________<br><br><br><br><br><br><br><br><br><br><br><br><br><br>____________________________________________<br>"
        # # BUG: I don't know how to set this template. Ideally I'd use selected cols
        # # and build out those, but the template appears to only accept x and y...
        # hovertemplate += f"{x_column}: %{{x}} <br>{y_column}: %{{y}}"
        # hovertemplate += "<extra></extra>"

        fig = px.scatter(
            data_frame=df,
            **plot_config,
            # custom_data=smiles_column,  # required for drawing mols on hover
        )

        # fig.update_traces(hovertemplate=hovertemplate)
        fig.update_layout(dragmode="zoom")

        return fig
