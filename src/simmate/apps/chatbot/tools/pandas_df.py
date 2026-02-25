# -*- coding: utf-8 -*-

import pandas
from langchain.agents.agent_types import AgentType
from langchain.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from simmate.configuration import settings

from ..llm import get_llm


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
