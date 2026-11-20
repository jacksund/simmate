import json
import random

from django.contrib.auth.models import User

from ..models import Candidate, Leaderboard, Matchup

DEBATE_INSTRUCTIONS = """
You are judging which of two candidates better meets the objective of a
leaderboard. Compare them only against the leaderboard's objective and
description, using what is known about each candidate (its identity, any
results in its metadata, and users' comments). A leaderboard's objective can
build on the objectives of its parent leaderboards, which are listed first.
When information is missing, reason from the chemistry itself and say what you
assumed. Declare a draw only when the two are truly equal for this leaderboard.
"""

RESULT_SCHEMA = {
    "title": "matchup_result",
    "description": "The winner of the matchup and why.",
    "type": "object",
    "properties": {
        "rationale": {
            "type": "string",
            "description": "A short argument for the decision, comparing both candidates.",
        },
        "winner": {
            "type": "string",
            "enum": ["A", "B", "draw"],
            "description": "Which candidate better meets the leaderboard's objective.",
        },
    },
    "required": ["rationale", "winner"],
}


def run_debate(
    leaderboard: Leaderboard,
    candidate_a: Candidate = None,
    candidate_b: Candidate = None,
    user: User = None,
) -> Matchup:
    """
    Has the llm judge which of two candidates better meets the leaderboard's
    objective, and then records the result as a matchup (which updates both
    candidates' ratings).

    Args:
        leaderboard: The leaderboard that both candidates belong to.
        candidate_a: The first candidate. If either candidate is not given,
            the pair is chosen by the leaderboard's rating system.
        candidate_b: The second candidate.
        user: The user that started the debate.

    Returns:
        The new `Matchup`.
    """
    if not candidate_a or not candidate_b:
        candidates = list(
            leaderboard.candidates.select_related(
                "substance__molecule",
                "substance__structure",
                "mixture",
            )
        )
        candidate_a, candidate_b = leaderboard.get_rating_system().pick_pair(candidates)

    # The candidates are put in a random order to avoid any bias toward the
    # first (or second) one listed
    if random.random() < 0.5:
        candidate_a, candidate_b = candidate_b, candidate_a

    descriptions = {}
    for candidate in [candidate_a, candidate_b]:
        info = {"id": candidate.display_id}
        if candidate.is_mixture:
            mixture = candidate.mixture
            info["mixture_type"] = mixture.mixture_type
            info["common_name"] = mixture.common_name
            info["description"] = mixture.description
            info["components"] = [
                {
                    "substance_id": part.substance_id,
                    "common_name": part.substance.common_name,
                    "smiles": (
                        part.substance.molecule.smiles
                        if part.substance.molecule
                        else None
                    ),
                    "role": part.role,
                    "amount": part.amount,
                    "amount_units": part.amount_units,
                }
                for part in mixture.components.select_related("substance__molecule")
            ]
        else:
            substance = candidate.substance
            info["substance_id"] = substance.id
            info["substance_type"] = substance.substance_type
            info["common_name"] = substance.common_name
            info["description"] = substance.description
            if substance.molecule:
                info["smiles"] = substance.molecule.smiles
            if substance.structure:
                info["formula"] = substance.structure.formula_reduced
                info["spacegroup"] = substance.structure.spacegroup_id
        info["metadata"] = candidate.metadata
        info["comments"] = candidate.comments
        descriptions[candidate.id] = info

    # Child objectives often say "Same as <parent>, plus ...", so the parent
    # leaderboards' objectives are given too (from the top level down)
    # (objectives aren't loaded by `get_path`, so each is a quick extra query)
    parents = [board for board in leaderboard.get_path()[:-1] if board.objective]
    parent_objectives = "".join(
        f"## Parent leaderboard: {board.name}\n{board.objective}\n\n"
        for board in parents
    )

    prompt = (
        f"{DEBATE_INSTRUCTIONS}\n"
        f"# Leaderboard: {leaderboard.name}\n\n"
        f"{parent_objectives}"
        f"## Objective\n{leaderboard.objective or '(none given)'}\n\n"
        f"## Description\n{leaderboard.description or '(none given)'}\n\n"
        f"# Candidate A\n{json.dumps(descriptions[candidate_a.id], indent=2, default=str)}\n\n"
        f"# Candidate B\n{json.dumps(descriptions[candidate_b.id], indent=2, default=str)}\n"
    )

    # local import because langchain is an optional dependency (the `chatbot` extra)
    from simmate.apps.chatbot.llm import get_llm

    llm = get_llm().with_structured_output(RESULT_SCHEMA)
    result = llm.invoke(prompt)

    score_a = {"A": 1.0, "B": 0.0, "draw": 0.5}[result["winner"]]

    return leaderboard.record_matchup(
        candidate_a=candidate_a,
        candidate_b=candidate_b,
        score_a=score_a,
        judge_type="llm-debate",
        rationale=result["rationale"],
        user=user,
    )
