# -*- coding: utf-8 -*-

import streamlit
from pandas import DataFrame


def get_streamlit_dataframe(dataframe_id: int) -> DataFrame:
    """
    Grabs the appropriate DataFrame from the current streamlit session state.
    The chat history should be analyzed in order to select the appropriate
    dataframe_id. For example, if you determine the correct dataframe is
    designated by "(( DATAFRAME 1 ))" in the chat history, then your response
    should be the number 1. If you don't think the necessary dataset is present,
    return -1. If there is only one dataframe, use that one.
    """

    # BUG: handle -1 being returned, which means the dataset is not present.
    df = streamlit.session_state.dataframes[dataframe_id]

    return df
