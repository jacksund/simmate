# -*- coding: utf-8 -*-

from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function

from .prompts import agent_prompt
from .tools import simmate_tools
from .utilities import get_llm

llm = get_llm()

# This would replace code below, but has the following bug:
#   https://github.com/langchain-ai/langchain/issues/19843
# from langchain.agents import create_tool_calling_agent
# simmate_agent = create_tool_calling_agent(
#     llm=llm,
#     tools=simmate_tools,
#     prompt=agent_prompt,
# )

llm_with_tools = llm.bind(
    functions=[convert_to_openai_function(t) for t in simmate_tools]
)

simmate_agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | agent_prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)
