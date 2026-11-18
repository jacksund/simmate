from django.db import migrations


def delete_candidates_and_matchups(apps, schema_editor):
    # Candidates move from projects to leaderboards (see the next migration).
    # Existing ones were only test data, so they are deleted instead of being
    # moved over. This is its own migration because Postgres won't alter a
    # table in the same transaction that deleted rows from it.
    apps.get_model("project_management", "Matchup").objects.all().delete()
    apps.get_model("project_management", "Candidate").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("project_management", "0003_candidates_and_matchups"),
    ]

    operations = [
        migrations.RunPython(
            delete_candidates_and_matchups,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
