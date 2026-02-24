# -*- coding: utf-8 -*-

from langchain.tools import tool

from ..llm import get_llm

LOOKUP_PROMPT = """
Please provide the CAS Number for the following chemical compound: 
- {compound_name}

Return your response strictly in the following JSON format:
{{"cas_number": "string", "confidence": integer, "comment": "string or null"}}

Guidelines:
- cas_number: Provide the standard hyphenated CAS number.
- confidence: An integer from 0–100 representing your certainty that this specific CAS number matches the compound name.
- comment: If confidence is 100, set this to null. If confidence is below 100, provide a brief explanation (e.g., potential isomers, ambiguous naming, or multiple registry numbers).

Do not include any text, headers, or explanations outside of the JSON object.
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
    filled_prompt = LOOKUP_PROMPT.format(compound_name=compound_name)
    response = llm.invoke(filled_prompt)
    return response.content
