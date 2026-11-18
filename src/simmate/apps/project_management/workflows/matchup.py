from django.contrib.auth.models import User

from simmate.utils import logger
from simmate.workflows import Workflow

from ..ai import run_debate
from ..models import Candidate, Leaderboard


class CandidateDebate__Llm__Matchup(Workflow):
    """
    Has an llm judge which of two candidates in a leaderboard better meets the
    leaderboard's objective. The result is saved as a `Matchup`, which updates both
    candidates' ratings.

    If the candidates are not given, the leaderboard's rating system picks
    the next pair.
    """

    description_doc_short = "an llm judges a matchup of two leaderboard candidates"

    @staticmethod
    def run_config(
        leaderboard_id: int,
        candidate_a_id: int = None,
        candidate_b_id: int = None,
        user_id: int = None,
        **kwargs,
    ) -> int:
        leaderboard = Leaderboard.objects.get(id=leaderboard_id)
        matchup = run_debate(
            leaderboard=leaderboard,
            candidate_a=(
                Candidate.objects.get(id=candidate_a_id) if candidate_a_id else None
            ),
            candidate_b=(
                Candidate.objects.get(id=candidate_b_id) if candidate_b_id else None
            ),
            user=User.objects.get(id=user_id) if user_id else None,
        )
        winner = matchup.winner.display_id if matchup.winner else "draw"
        logger.info(
            f"{matchup.display_id}: {matchup.candidate_a.display_id} vs "
            f"{matchup.candidate_b.display_id} (winner: {winner})"
        )
        return matchup.id
