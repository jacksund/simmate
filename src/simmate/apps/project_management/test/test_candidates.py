from types import SimpleNamespace

import pytest
from django.urls import reverse

from simmate.apps.inventory_management.models import Substance
from simmate.apps.project_management.models import (
    Candidate,
    Leaderboard,
    Matchup,
    Project,
    ProjectComponent,
)
from simmate.apps.project_management.ratings import Elo, Glicko


def test_rating_systems():
    # two new candidates, where A wins
    a = SimpleNamespace(rating=1500, rating_deviation=350)
    b = SimpleNamespace(rating=1500, rating_deviation=350)
    Glicko().update(a, b, score_a=1)
    assert a.rating == pytest.approx(1662.2, abs=0.1)
    assert b.rating == pytest.approx(1337.8, abs=0.1)
    assert a.rating_deviation == pytest.approx(290.2, abs=0.1)

    a = SimpleNamespace(rating=1500)
    b = SimpleNamespace(rating=1500)
    Elo().update(a, b, score_a=1)
    assert (a.rating, b.rating) == (1516, 1484)

    # draws between equal ratings change nothing
    a = SimpleNamespace(rating=1500)
    b = SimpleNamespace(rating=1500)
    Elo().update(a, b, score_a=0.5)
    assert (a.rating, b.rating) == (1500, 1500)


@pytest.mark.django_db
def test_matchups_and_recalculate(admin_client):
    batteries = Leaderboard.objects.create(name="Batteries")
    leaderboard = Leaderboard.objects.create(
        name="Cathodes",
        objective="Highest voltage",
        parent_leaderboard=batteries,
    )
    candidates = [
        Candidate.objects.create(
            leaderboard=leaderboard,
            substance=Substance.objects.create(id=f"BCD-012-000{i}"),
        )
        for i in range(3)
    ]
    # new candidates start with the leaderboard's initial rating
    assert candidates[0].rating == 1500
    assert candidates[0].rating_deviation == 350

    # the most uncertain candidate is paired with the closest rating
    first, second = leaderboard.get_rating_system().pick_pair(candidates)
    assert first.id != second.id

    matchup = leaderboard.record_matchup(
        candidates[0], candidates[1], score_a=1, judge_type="manual"
    )
    leaderboard.record_matchup(
        candidates[0], candidates[2], score_a=0.5, judge_type="manual"
    )
    candidates[0].refresh_from_db()
    assert candidates[0].num_matchups == 2
    assert candidates[0].rating > 1500
    assert matchup.winner.id == candidates[0].id
    assert matchup.ratings_before["a"]["rating"] == 1500

    # switching rating systems replays all matchups
    glicko_rating = candidates[0].rating
    leaderboard.rating_system = "elo"
    leaderboard.save()
    leaderboard.recalculate_ratings()
    candidates[0].refresh_from_db()
    assert candidates[0].rating != glicko_rating
    assert candidates[0].rating_deviation is None
    assert candidates[0].num_matchups == 2

    # candidates from other leaderboards can't be matched up
    with pytest.raises(Exception, match="is not in leaderboard"):
        batteries.record_matchup(candidates[0], candidates[1], 1, "manual")

    # projects pick from leaderboards through their components
    project = Project.objects.create(name="Zeus")
    component = ProjectComponent.objects.create(
        project=project,
        name="Cathode",
        leaderboard=leaderboard,
        chosen_candidate=candidates[1],
    )

    # pages render
    for table, entry_id in [
        (Project.table_name, project.id),
        (Leaderboard.table_name, leaderboard.id),
        (Leaderboard.table_name, batteries.id),
        (ProjectComponent.table_name, component.id),
        (Candidate.table_name, candidates[0].id),
        (Matchup.table_name, matchup.id),
        (Substance.table_name, candidates[0].substance_id),
    ]:
        url = reverse("data_explorer:table-entry", args=[table, entry_id])
        assert admin_client.get(url).status_code == 200
    for table in [Candidate.table_name, Matchup.table_name]:
        url = reverse("data_explorer:table", args=[table])
        assert admin_client.get(url).status_code == 200
        url = reverse("data_explorer:table-entry-new", args=[table])
        query = {"leaderboard_id": leaderboard.id}
        assert admin_client.get(url, query).status_code == 200
    for table in [Leaderboard.table_name, ProjectComponent.table_name]:
        url = reverse("data_explorer:table", args=[table])
        assert admin_client.get(url).status_code == 200
        url = reverse("data_explorer:table-entry-new", args=[table])
        assert admin_client.get(url).status_code == 200
    for table, entry_id in [
        ("Project", project.id),
        ("Leaderboard", leaderboard.id),
        ("ProjectComponent", component.id),
    ]:
        url = reverse("data_explorer:table-entry-update", args=[table, entry_id])
        assert admin_client.get(url).status_code == 200


@pytest.mark.django_db
def test_substance_merge_moves_candidates():
    leaderboard = Leaderboard.objects.create(name="Cathodes")
    keep = Substance.objects.create(id="BCD-012-3456")
    dup = Substance.objects.create(id="BCD-012-0001")
    candidate = Candidate.objects.create(leaderboard=leaderboard, substance=dup)

    Substance.merge([dup.id], into=keep.id, reason="duplicate")

    candidate.refresh_from_db()
    assert candidate.substance_id == keep.id
    assert list(keep.leaderboards) == [leaderboard]
