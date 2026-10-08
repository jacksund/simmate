from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory_management", "0006_alter_batch_total_current_amount_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="batch",
            old_name="num_containers",
            new_name="num_available_containers",
        ),
    ]
