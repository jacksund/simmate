# -*- coding: utf-8 -*-

from langchain.agents import create_agent

from .llm import get_llm
from .tools import simmate_tools

llm = get_llm()

agent = create_agent(
    model=llm,
    tools=simmate_tools,
    system_prompt="You are a helpful assistant that uses tools when needed.",
)
