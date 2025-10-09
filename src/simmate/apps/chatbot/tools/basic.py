# -*- coding: utf-8 -*-

from langchain.agents import tool

from ..utilities import get_llm


@tool
def ask_general_question(question: str) -> str:
    """
    Answers any general questions using a basic text call to an LLM. Use this
    tool if the user is asking general knowledge questions where the other
    tools don't apply
    """
    llm = get_llm()
    response = llm.invoke(question)
    return response.content
