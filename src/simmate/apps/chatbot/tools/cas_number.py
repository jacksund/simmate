# -*- coding: utf-8 -*-

import json

from langchain.tools import tool

from simmate.apps.cas_registry.client import CasRegistryClient
from simmate.apps.cas_registry.models import CasRegistryMolecule
from simmate.apps.pubchem.client import PubChemClient

from ..llm import get_llm
from .web_search import search_web_for_context

CHEMICAL_NAMES_PROMPT = """
Here is a compound name and/or description: {compound_name}

Convert this to a list of chemical names suitable for searching PubChem with. 
Include the name as-is if it is already appropriate. Your list should include
the IUPAC name if possible. Only give a maximum of 5 different names. Order
the names so that the one most likely to give an accurate PubChem search result
comes first.

Respond with only the list of chemical names, separated with semicolons (;).
"""

LOOKUP_PROMPT = """
Please provide the CAS Number for the following chemical compound: {compound_name}

Return your response strictly in the following JSON format:
{{"cas_number": "string", "confidence": integer, "comment": "string or null"}}

Guidelines:
- cas_number: Provide the standard hyphenated CAS number. Or null if it cannot be found.
- confidence: An integer from 0–100 representing your certainty that this specific CAS number matches the compound name.
- comment: Provide a brief explanation such as the source of your confidence (e.g., where you found the CAS) or why confidence is below 100 (e.g., potential isomers, ambiguous naming, or multiple registry numbers).

Do not include any text, headers, codeblock, or explanations besides the JSON object.

Use the context below in assist in your answer. The context is pulled from a web search:

{web_context}
"""

VALIDATION_PROMPT = """
I am looking for the CAS number for {compound_name}.
I found the CAS number {cas_number}, which corresponds to the following name(s) in the CAS registry:
- Common Name: {common_name}
- Synonyms: {synonyms}

Is it highly likely that {compound_name} and the names from the CAS registry refer to the same chemical compound?
Consider synonyms, IUPAC names, and common names.

Respond with only a JSON object:
{{"is_match": boolean, "confidence": integer, "comment": "string"}}

Guidelines:
- is_match: true if the names refer to the same compound, false otherwise.
- confidence: An integer from 0–100 representing your certainty of the match.
- comment: Provide a brief explanation for your decision.
"""


def parse_json_response(content: str) -> dict:
    """Extracts and parses JSON from a string, handling markdown blocks."""
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]
    try:
        return json.loads(content.strip())
    except Exception:
        raise ValueError(f"Invalid JSON response: {content}")


@tool
def lookup_cas_number(compound_name: str, clean_name: bool = False) -> dict:
    """
    Search for the CAS (Chemical Abstracts Service) Registry Number of a given chemical compound.
    """

    llm = get_llm()

    # 0. convert to list of names that are robust to searching in dbs/apis
    if clean_name:
        filled_prompt = CHEMICAL_NAMES_PROMPT.format(compound_name=compound_name)
        response_content = llm.invoke(filled_prompt).content
        names = [n.strip() for n in response_content.split(";")]
    else:
        names = [compound_name]

    # Only use the first name for now:
    compound_name_clean = names[0]

    # 1. check if we already have this in the simmate db
    query = CasRegistryMolecule.objects.filter(common_name=compound_name_clean)
    if query.exists():
        return {
            "cas_number": query.first().id,
            "confidence": 100,
            "comment": (
                "This was pulled directly from the Simmate database's CAS Reg. cache, "
                "where the cache is populated directly from the official CAS API."
            ),
        }

    # 2. search cas api
    results = CasRegistryClient.search(query=compound_name_clean, size=1)
    if results:
        return {
            "cas_number": results[0]["rn"],
            "confidence": 100,
            "comment": "Found this CAS number by searching the official CAS API",
        }

    # 3. search pubchem api
    try:
        cid_data = PubChemClient.get_data_from_name(compound_name_clean)
        if cid_data["cas_number"]:
            return {
                "cas_number": cid_data["cas_number"],
                "confidence": 90,
                "comment": (
                    "Found using PubChem API name search. However, PubChem often "
                    "has multiple CAS numbers listed for a given compound, so this "
                    "is not guaranteed to be correct."
                ),
            }
    except Exception:
        pass

    # 4. do a deeper web search
    try:
        web_context = search_web_for_context.run(
            f"What is the CAS number for {compound_name_clean}?"
        )
    except Exception:
        web_context = "(no search results recieved)"

    filled_prompt = LOOKUP_PROMPT.format(
        compound_name=compound_name_clean,
        web_context=web_context,
    )
    response = llm.invoke(filled_prompt)
    response_data = parse_json_response(response.content)

    # 5. Validate by looking up in CAS API + asking LLM to confirm name match
    cas_number = response_data.get("cas_number")
    if not cas_number:
        return response_data

    try:
        cas_detail = CasRegistryClient.detail(cas_number)
    except Exception:
        # If lookup fails, it's a major red flag
        return {
            **response_data,
            "confidence": min(response_data.get("confidence", 100), 10),
            "comment": f"Note: CAS {cas_number} was found via web but not in official registry.",
        }

    # Ask the LLM to confirm if the name from the CAS registry matches the compound
    cas_common_name = cas_detail.get("name")
    cas_synonyms = cas_detail.get("synonyms", [])

    filled_validation_prompt = VALIDATION_PROMPT.format(
        compound_name=compound_name_clean,
        cas_number=cas_number,
        common_name=cas_common_name,
        synonyms="; ".join(cas_synonyms) if cas_synonyms else "(none listed)",
    )
    validation_response = llm.invoke(filled_validation_prompt)
    validation_data = parse_json_response(validation_response.content)
    if validation_data.get("is_match"):
        return {
            **response_data,
            "confidence": validation_data.get(
                "confidence", response_data["confidence"]
            ),
            "comment": validation_data.get("comment", response_data["comment"]),
        }
    else:
        return {
            **response_data,
            "confidence": min(validation_data.get("confidence", 20), 20),
            "comment": f"Validation failed: {validation_data.get('comment', '')} (Registry name: {cas_common_name})",
        }
