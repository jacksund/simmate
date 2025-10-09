# -*- coding: utf-8 -*-

from langchain.agents import tool
from pandas import DataFrame

from ..chains import get_ask_db_chain, get_data_from_db_chain


@tool(return_direct=True)
def get_dataframe_from_database(question: str) -> DataFrame:
    """
    Will load the appropriate dataframe from the Simmate production database.

    Use this tool when the user wants a dataset loaded and returned to them.
    Do not use when the user's question is based on counting, metadata, or
    summaries.
    """
    sql_result = get_data_from_db_chain().run(question)
    df = DataFrame(sql_result)
    return df


@tool
def get_answer_from_database(question: str) -> DataFrame:
    """
    Answers a question about data in the Simmate database.

    Note, this tool is best for questions that can be answered using a single
    SQL query, which often pertain to counting and/or metadata questions.
    """
    return get_ask_db_chain().run(question)
