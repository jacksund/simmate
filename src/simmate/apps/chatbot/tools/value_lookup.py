# -*- coding: utf-8 -*-

from langchain.tools import tool
from langchain_core.prompts import PromptTemplate

from ..utilities import get_llm

LOOKUP_PROMPT = """
Please provide the {lookup_name} for the chemical compound: {compound_name}.

Return your response strictly in the following JSON format:
{{"{lookup_name}": "string", "confidence": integer, "comment": "string or null"}}

Guidelines:
- cas_number: Provide the standard hyphenated CAS number.
- confidence: An integer from 0–100 representing your certainty that this {lookup_name} is correct for the compound. 100 is only allowed when you have a source.
- comment: If confidence is 100, set this to null. If confidence is below 100, provide a brief explanation.

Do not include any text, headers, or explanations outside of the JSON object.
"""


@tool
def value_lookup(lookup_name: str, compound_name: str) -> dict:
    # example:
    # value_lookup.invoke(dict(lookup_name="pubchem_cid", compound_name="Aluminum Oxide"))

    llm = get_llm()
    filled_prompt = PromptTemplate.from_template(LOOKUP_PROMPT).format(
        lookup_name=lookup_name,
        compound_name=compound_name,
    )
    response = llm.invoke(filled_prompt)
    return response.content
