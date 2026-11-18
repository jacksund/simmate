class RatingSystem:
    """
    Base class for how a project's candidates are rated.

    The default approach is pairwise: two candidates are compared in a
    `Matchup` (e.g. an llm debate), and the result updates both of their
    ratings. Subclasses (e.g. `Elo` and `Glicko`) set the starting values and
    the update math.

    A rating system only works with a candidate's rating columns (`rating`,
    `rating_deviation`, `rating_data`, and `num_matchups`) and never saves
    anything to the database. Saving is handled by `Project.record_matchup`.

    Custom fitness functions can be added later as subclasses too. These can
    override `update` and `pick_pair`, or score each candidate on its own
    instead of through matchups.
    """

    def initial_state(self) -> dict:
        """
        Gives the rating columns that a new candidate starts with.

        Returns:
            A dictionary of `rating`, `rating_deviation`, and `rating_data`.
        """
        raise NotImplementedError()

    def update(self, candidate_a, candidate_b, score_a: float):
        """
        Sets the new rating columns on both candidates after a matchup. This
        does not save the candidates.

        Args:
            candidate_a: The first candidate of the matchup.
            candidate_b: The second candidate of the matchup.
            score_a: The result for candidate A, where 1 is a win, 0.5 is a
                draw, and 0 is a loss.
        """
        raise NotImplementedError()

    def pick_pair(self, candidates: list) -> tuple:
        """
        Chooses the two candidates to compare next.

        By default, this takes the candidate with the fewest matchups and pairs
        it with the candidate closest to it in rating.

        Args:
            candidates: All candidates to choose from (at least two).

        Returns:
            The two candidates as (candidate_a, candidate_b).
        """
        if len(candidates) < 2:
            raise Exception("At least two candidates are needed for a matchup.")
        first = min(candidates, key=lambda c: c.num_matchups)
        second = min(
            [c for c in candidates if c.id != first.id],
            key=lambda c: abs(c.rating - first.rating),
        )
        return first, second
