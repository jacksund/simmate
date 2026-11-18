from .base import RatingSystem


class Elo(RatingSystem):
    """
    The classic Elo rating system, where each candidate has a single rating.

    The expected score of A against B is:
        E_A = 1 / (1 + 10^((R_B - R_A) / 400))

    And after a matchup, each rating moves by:
        R_A' = R_A + K * (S_A - E_A)
    """

    initial_rating: float = 1500
    """
    The rating that every new candidate starts with.
    """

    k_factor: float = 32
    """
    The largest amount that a rating can change in a single matchup.
    """

    def initial_state(self) -> dict:
        return {
            "rating": self.initial_rating,
            "rating_deviation": None,
            "rating_data": None,
        }

    def update(self, candidate_a, candidate_b, score_a: float):
        expected_a = 1 / (1 + 10 ** ((candidate_b.rating - candidate_a.rating) / 400))
        change = self.k_factor * (score_a - expected_a)
        candidate_a.rating += change
        candidate_b.rating -= change
