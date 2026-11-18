import math

from .base import RatingSystem


class Glicko(RatingSystem):
    """
    The Glicko-1 rating system, where each candidate has a rating and a
    rating deviation (RD).

    The RD is how uncertain the rating is. It starts high, so a new candidate's
    rating moves quickly over its first few matchups, and it shrinks with each
    matchup. It is also how the leaderboard shows confidence (e.g. a candidate
    is roughly within `rating ± 2 * RD`).

    Each matchup is treated as its own rating period. RDs do not grow back over
    time (i.e. Glicko's `c` constant is not used yet).

    See http://www.glicko.net/glicko/glicko.pdf for the math.
    """

    initial_rating: float = 1500
    """
    The rating that every new candidate starts with.
    """

    initial_deviation: float = 350
    """
    The RD that every new candidate starts with (i.e. "no information").
    """

    min_deviation: float = 30
    """
    The smallest that an RD can shrink to, so that ratings can always move.
    """

    def initial_state(self) -> dict:
        return {
            "rating": self.initial_rating,
            "rating_deviation": self.initial_deviation,
            "rating_data": None,
        }

    def update(self, candidate_a, candidate_b, score_a: float):
        q = math.log(10) / 400

        # both updates use the ratings from before this matchup
        players = [
            (candidate_a, candidate_b, score_a),
            (candidate_b, candidate_a, 1 - score_a),
        ]
        new_values = []
        for player, opponent, score in players:
            # g() lowers the impact of opponents with uncertain ratings
            g = 1 / math.sqrt(1 + 3 * q**2 * opponent.rating_deviation**2 / math.pi**2)
            expected = 1 / (1 + 10 ** (-g * (player.rating - opponent.rating) / 400))
            d_squared = 1 / (q**2 * g**2 * expected * (1 - expected))
            precision = 1 / player.rating_deviation**2 + 1 / d_squared
            new_values.append(
                (
                    player.rating + q / precision * g * (score - expected),
                    max(math.sqrt(1 / precision), self.min_deviation),
                )
            )

        for player, (rating, deviation) in zip([candidate_a, candidate_b], new_values):
            player.rating = rating
            player.rating_deviation = deviation

    def pick_pair(self, candidates: list) -> tuple:
        # the most uncertain candidate goes first, paired with the closest rating
        if len(candidates) < 2:
            raise Exception("At least two candidates are needed for a matchup.")
        first = max(candidates, key=lambda c: c.rating_deviation)
        second = min(
            [c for c in candidates if c.id != first.id],
            key=lambda c: abs(c.rating - first.rating),
        )
        return first, second
