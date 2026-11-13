import time

from simmate.compute import WorkItem
from simmate.utils import logger
from simmate.workflows import Workflow

from ..models import Project
from .matchup import CandidateDebate__Llm__Matchup


class CandidateDebate__Llm__Tournament(Workflow):
    """
    Runs many llm debates between a project's candidates, which builds up the
    project's leaderboard.

    This keeps a steady number of debates (`nsteadystate`) submitted to workers
    at all times, until `max_matchups` debates have been submitted and have
    finished. Each debate is its own `candidate-debate.llm.matchup` run.

    Pairs are picked by the project's rating system when each debate is
    submitted. A candidate is only in one running debate at a time, so its
    rating is always up to date when it is next picked.
    """

    description_doc_short = "keeps llm debates running to rate a project's candidates"

    @staticmethod
    def run_config(
        project_id: int,
        max_matchups: int = 100,
        nsteadystate: int = 5,
        sleep_step: int = 10,
        debate_tags: list[str] = [],
        **kwargs,
    ):
        project = Project.objects.get(id=project_id)
        rating_system = project.get_rating_system()
        logger.info(
            f"Starting a tournament of {max_matchups} debates for project "
            f"{project.name}, with {nsteadystate} running at a time."
        )

        running = {}  # WorkItem id -> the ids of its two candidates
        nsubmitted = 0
        while True:
            # drop debates that have finished (interrupted ones will be retried
            # by workers, so they are still counted as running)
            still_running = set(
                WorkItem.objects.filter(
                    id__in=list(running),
                    status__in=WorkItem.active_statuses + ["Interrupted"],
                ).values_list("id", flat=True)
            )
            running = {
                workitem_id: pair
                for workitem_id, pair in running.items()
                if workitem_id in still_running
            }

            if nsubmitted >= max_matchups and not running:
                break

            # top up to our steady-state, using candidates that aren't already
            # in a running debate
            busy_ids = {
                candidate_id for pair in running.values() for candidate_id in pair
            }
            free = list(project.candidates.exclude(id__in=busy_ids))
            while len(running) < nsteadystate and nsubmitted < max_matchups:
                if len(free) < 2:
                    break  # wait for running debates to free up candidates
                candidate_a, candidate_b = rating_system.pick_pair(free)
                state = CandidateDebate__Llm__Matchup.run_cloud(
                    project_id=project.id,
                    candidate_a_id=candidate_a.id,
                    candidate_b_id=candidate_b.id,
                    tags=debate_tags,
                )
                # NOTE: this is the WorkItem id and NOT the run_id
                running[state.pk] = (candidate_a.id, candidate_b.id)
                free = [c for c in free if c.id not in running[state.pk]]
                nsubmitted += 1

            if not running:
                logger.warning("The project needs at least two candidates.")
                break

            time.sleep(sleep_step)

        logger.info(f"Tournament finished after {nsubmitted} debates.")
