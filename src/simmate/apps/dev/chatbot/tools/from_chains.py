# -*- coding: utf-8 -*-

from langchain.agents import tool

from ..chains import ask_docs_chain


@tool
def ask_docs_tool(question: str):
    """
    Given a question about Simmate, this will search the documentation and
    return an answer.
    """
    response = ask_docs_chain.invoke(question)
    return response
