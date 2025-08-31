# -*- coding: utf-8 -*-

import pandas
from langchain.agents import tool
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from simmate.configuration import settings

from ..utilities import get_llm


@tool
def analyze_dataframe(question: str, dataset: dict) -> str:
    """
    Answers a question about a dataset. The dataset must be provided as a
    dictionary.
    """
    # chatbots require json-serialized inputs & outputs, so we need to accept
    # the input as a dict and convert to a pandas dataframe
    df = pandas.DataFrame.from_dict(dataset)

    llm = get_llm()
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=settings.chatbot.verbose,
        agent_type=AgentType.OPENAI_FUNCTIONS,  # !!! not sure if this is needed
    )
    response = agent.invoke(question)
    return response["output"]


# FOR TESTING ONLY -- TO BE DEPRECIATED
@tool(return_direct=True)
def get_titanic_dataset() -> pandas.DataFrame:
    """
    Loads a dataset on the Titanic's Passengers.

    To the chatbot: This should only be used when loading the dataset. If you
    see dataframes already in chat history (e.g., "(( DATAFRAME 2 ))"), then
    do not call this tool again
    """
    return pandas.read_csv(
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/doc/data/titanic.csv"
    )
