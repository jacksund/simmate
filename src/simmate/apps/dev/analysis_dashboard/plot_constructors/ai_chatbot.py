# -*- coding: utf-8 -*-

import pandas as pd
import streamlit as st

from simmate.apps.dev.chatbot.plotly import get_plotly_figure

from .base import PlotConstructor


class AiChatbotFigure(PlotConstructor):

    display_name = "Describe to AI"
    required_inputs = ["user_request"]

    @staticmethod
    def get_inputs(df: pd.DataFrame) -> dict:
        return {
            "user_request": st.text_input(
                label="Type in your request:",
                placeholder="A scatter plot of...",
                value=None,
            ),
        }

    @classmethod
    def get_plot(cls, df: pd.DataFrame, plot_config: dict):
        fig = get_plotly_figure(
            df=df,
            **plot_config,
            # using the cache is important for when the user applies filters
            # because otherwise we would need to call the LLM again.
            use_cache=True,
        )
        return fig
