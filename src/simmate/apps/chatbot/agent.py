# -*- coding: utf-8 -*-

from langchain.agents import create_agent

from .llm import get_llm
from .tools import lookup_cas_number


def get_agent():

    llm = get_llm()

    # (optional) enable built in tools that come with google ai studio
    # web_tools = [
    #     {"url_context": {}},
    #     {"google_search": {}},
    # ] if "provider" == "Google-GenAI" else []

    return create_agent(
        model=llm,
        tools=[
            lookup_cas_number,
            # *google_tools,
        ],
        system_prompt="You are a helpful assistant that uses tools when needed.",
    )

    # then you call with something like...
    # agent.invoke(
    #     {"messages": [{"role": "user", "content": "What is the CAS for aluminum oxide?"}]}
    # )
