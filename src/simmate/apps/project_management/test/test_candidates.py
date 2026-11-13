from types import SimpleNamespace

import pytest
from django.urls import reverse

from simmate.apps.inventory_management.models import Substance
from simmate.apps.project_management.models import Candidate, Matchup, Project
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
    project = Project.objects.create(name="Zeus", objective="Highest voltage")
    candidates = [
        Candidate.objects.create(
            project=project,
            substance=Substance.objects.create(id=f"BCD-012-000{i}"),
        )
        for i in range(3)
    ]
    # new candidates start with the project's initial rating
    assert candidates[0].rating == 1500
    assert candidates[0].rating_deviation == 350

    # the most uncertain candidate is paired with the closest rating
    first, second = project.get_rating_system().pick_pair(candidates)
    assert first.id != second.id

    matchup = project.record_matchup(
        candidates[0], candidates[1], score_a=1, judge_type="manual"
    )
    project.record_matchup(
        candidates[0], candidates[2], score_a=0.5, judge_type="manual"
    )
    candidates[0].refresh_from_db()
    assert candidates[0].num_matchups == 2
    assert candidates[0].rating > 1500
    assert matchup.winner.id == candidates[0].id
    assert matchup.ratings_before["a"]["rating"] == 1500

    # switching rating systems replays all matchups
    glicko_rating = candidates[0].rating
    project.rating_system = "elo"
    project.save()
    project.recalculate_ratings()
    candidates[0].refresh_from_db()
    assert candidates[0].rating != glicko_rating
    assert candidates[0].rating_deviation is None
    assert candidates[0].num_matchups == 2

    # candidates from other projects can't be matched up
    other = Project.objects.create(name="Athena")
    with pytest.raises(Exception, match="is not in project"):
        other.record_matchup(candidates[0], candidates[1], 1, "manual")

    # pages render
    for table, entry_id in [
        (Project.table_name, project.id),
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
        assert admin_client.get(url, {"project_id": project.id}).status_code == 200
    url = reverse("data_explorer:table-entry-update", args=["Project", project.id])
    assert admin_client.get(url).status_code == 200


@pytest.mark.django_db
def test_substance_merge_moves_candidates():
    project = Project.objects.create(name="Zeus")
    keep = Substance.objects.create(id="BCD-012-3456")
    dup = Substance.objects.create(id="BCD-012-0001")
    candidate = Candidate.objects.create(project=project, substance=dup)

    Substance.merge([dup.id], into=keep.id, reason="duplicate")

    candidate.refresh_from_db()
    assert candidate.substance_id == keep.id
    assert list(keep.projects) == [project]
