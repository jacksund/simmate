# -*- coding: utf-8 -*-

import json

from langchain.tools import tool

from ..llm import get_llm
from .web_search import search_web_for_context

SIMPLIFY_PROMPT = """
Here is a compound name and/or description: {compound_name}

Convert this to a chemical name suitable for searching a web form or chemical 
synonyms database. Keep the name as-is if it is already appropriate. Do not 
simplify or alter specificity, as this will be used to look up the 
compound's CAS number.

Respond with only the chemical name.
"""

LOOKUP_PROMPT = """
Please provide the CAS Number for the following chemical compound: 
- {compound_name}

Return your response strictly in the following JSON format:
{{"cas_number": "string", "confidence": integer, "comment": "string or null"}}

Guidelines:
- cas_number: Provide the standard hyphenated CAS number. Or null if it cannot be found.
- confidence: An integer from 0–100 representing your certainty that this specific CAS number matches the compound name.
- comment: Provide a brief explanation such as a source or why confidence is below 100 (e.g., potential isomers, ambiguous naming, or multiple registry numbers).

Do not include any text, headers, or explanations outside of the JSON object.

Use the context below in assist in your answer. The context is pulled from a web search:

{web_context}
"""


@tool
def lookup_cas_number(compound_name: str) -> dict:
    """
    Search for the CAS (Chemical Abstracts Service) Registry Number of a given chemical compound.

    Args:
        compound_name (str): The common name, IUPAC name, or trade name of the chemical.

    Returns:
        dict: A dictionary containing the 'cas_number', a 'confidence' score (0-100),
              and a 'comment' explaining any ambiguity or alternative isomers.
    """

    llm = get_llm()

    # 0. convert to list of names that are robust to searching in dbs/apis
    filled_prompt = SIMPLIFY_PROMPT.format(compound_name=compound_name)
    compound_name_clean = llm.invoke(filled_prompt).content

    # 1. check if we already have this in the simmate db
    # TODO

    # 2. search the cas or pubchem web api
    # TODO

    # 3. do a deeper web search
    # TODO query web specifically for trusted sites like vendors/pubchem/cas
    try:
        web_context = search_web_for_context.run(
            f"What is the CAS number for {compound_name}"
        )
    except:
        web_context = "(no search results recieved)"

    filled_prompt = LOOKUP_PROMPT.format(
        compound_name=compound_name_clean,
        web_context=web_context,
    )
    response = llm.invoke(filled_prompt)
    # TODO: assert format
    return json.loads(response.content)
