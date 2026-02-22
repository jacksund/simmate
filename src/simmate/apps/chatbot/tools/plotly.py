# -*- coding: utf-8 -*-

import re

from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_experimental.tools.python.tool import PythonAstREPLTool, sanitize_input
from plotly.graph_objects import Figure

from ..utilities import get_llm


# ideally this would be a tool, but we only use it within get_plotly_script
def get_plotly_script(question: str, df_head: str) -> str:
    """
    Generate the pure-python script needed to generate the desired Figure
    """
    template = PromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = template.format(
        question=question,
        df_head=df_head,
    )

    llm = get_llm()
    response = llm.invoke(prompt)

    script = sanitize_input(extract_python_code(response.content))
    return script


def extract_python_code(text):
    pattern = r"```python\s(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return None
    else:
        return matches[0]


@tool(return_direct=True)
def get_plotly_figure(question: str, dataframe_id: int) -> Figure:
    """
    Generates a plot using a user's request/question and the id of the dataframe
    that should be used for source data.

    Utilize the user's question and the chat history to determine which
    dataframe_id is needed as an input for the request. Your answer should be the
    number associated with the dataframe_id that you think should be used. For
    example, if you determine the correct dataframe is designated by
    "(( DATAFRAME 1 ))" in the chat history, then the dataframe_id should be
    the number 1. If you don't think the necessary dataset is present or are
    unsure, set dataframe_id to -1.
    """

    # TODO: grab required dataframe based on user request
    import streamlit

    from .streamlit import get_streamlit_dataframe

    df = get_streamlit_dataframe(dataframe_id)

    # call llm to generate code based on user request
    script = get_plotly_script(question=question, df_head=df.head())
    # streamlit.code(script, language="python", line_numbers=True)  # for testing

    # Run the python code that the LLM provided
    python_repl = PythonAstREPLTool(
        globals={},
        locals={"df": df},
    )
    stdout = python_repl.run(script)
    # BUG: I should be able to use this lower level util instead of PythonAstREPLTool
    # but it doesn't properly pass locals for some reason
    #   from langchain_experimental.utilities import PythonREPL

    # Inspect the variables of the script run and grab the plotly figure
    final_figure = python_repl.locals.get("fig", None)

    if not final_figure:
        streamlit.write("Failed to generate figure. Try again.")
        streamlit.code(script, language="python", line_numbers=True)
        streamlit.code(stdout, language="python", line_numbers=True)
        return

    return final_figure


# Used this post as a starting point:
# https://g-giasemidis.medium.com/chat-with-and-visualise-your-data-part-i-40b7272a16d1
PROMPT_TEMPLATE = """
You are working with a pandas dataframe in Python. The name of the dataframe is `df`.
This is the result of `print(df.head())`:\n

{df_head}


Generate the python code <code> for plotting the previous data in plotly, in the 
format requested. Assume `df` is already available in the local variables, and 
make the final plotly figure available under the local variable name `fig`. The 
solution should be given using plotly and only plotly. Do not use matplotlib.
Do not include `fig.show()` and don't forget to import what you need from plotly
and pandas. Return the code <code> in the following format ```python <code>```.

Here is the user's question/request:

{question}
"""
