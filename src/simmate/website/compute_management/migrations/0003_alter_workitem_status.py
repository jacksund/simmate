from django.db import migrations, models

STATUS_MAP = {
    "P": "Pending",
    "R": "Running",
    "C": "Cancelled",
    "E": "Failed",
    "F": "Completed",
    "I": "Interrupted",
}


def letters_to_words(apps, schema_editor):
    WorkItem = apps.get_model("compute_management", "WorkItem")
    for old, new in STATUS_MAP.items():
        WorkItem.objects.filter(status=old).update(status=new)


def words_to_letters(apps, schema_editor):
    WorkItem = apps.get_model("compute_management", "WorkItem")
    for old, new in STATUS_MAP.items():
        WorkItem.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):

    dependencies = [
        ("compute_management", "0002_alter_workitem_status"),
    ]

    operations = [
        # widen the column first so the full status names fit
        migrations.AlterField(
            model_name="workitem",
            name="status",
            field=models.CharField(db_index=True, default="Pending", max_length=20),
        ),
        migrations.RunPython(letters_to_words, words_to_letters),
    ]
