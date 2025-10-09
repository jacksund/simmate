# -*- coding: utf-8 -*-

import re

import pandas as pd
from langchain.prompts import PromptTemplate
from langchain_experimental.tools.python.tool import PythonAstREPLTool, sanitize_input
from plotly.graph_objects import Figure

from simmate.utilities import get_hash_key

from .utilities import get_llm

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

{user_request}
"""

# This resets every time the python session is restarted. It primarily exists
# for the analysis dashboard, where we call these functions many times in
# succession with different df subsets (but same request and df.columns). As
# a result the `use_cache` kwarg helps us save on calling the LLM many times
# and just lets us reuse python scripts.
PLOTLY_SCRIPT_CACHE = {}


def get_plotly_script(
    user_request: str, df: pd.DataFrame, use_cache: bool = False
) -> str:
    """
    Generates a pure-python script needed to generate the desired Figure from
    a given pandas dataframe
    """

    text_to_hash = f"USER REQUEST: {user_request}\n DF_COLUMNS: {df.columns}"
    cache_key = get_hash_key(text_to_hash)
    if use_cache and cache_key in PLOTLY_SCRIPT_CACHE:
        return PLOTLY_SCRIPT_CACHE[cache_key]

    # Generate our message for the llm
    template = PromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = template.format(
        user_request=user_request,
        df_head=df.head(),  # Note we just want the header!
    )

    # Actually call the LLM and get the response
    llm = get_llm()
    response = llm.invoke(prompt)

    # We now need to extract the python code block from the LLM's reponse
    def extract_python_code(text):
        pattern = r"```python\s(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if not matches:
            return None
        else:
            return matches[0]

    script = sanitize_input(extract_python_code(response.content))

    # add to cache for future use
    if use_cache and cache_key not in PLOTLY_SCRIPT_CACHE:
        PLOTLY_SCRIPT_CACHE[cache_key] = script

    return script


def get_plotly_figure(
    user_request: str, df: pd.DataFrame, use_cache: bool = False
) -> Figure:
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

    # call llm to generate code based on user request
    script = get_plotly_script(
        user_request=user_request,
        df=df,
        use_cache=use_cache,
    )
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
        raise Exception("Failed to generate figure. Try again.")

    return final_figure
