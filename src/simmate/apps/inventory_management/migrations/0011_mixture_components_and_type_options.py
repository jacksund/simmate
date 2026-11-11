import django.db.models.deletion
from django.db import migrations, models

import simmate.database.core.archive

# old value --> new value
SUBSTANCE_TYPE_RENAMES = {
    "atomic_ion": "monatomic_ion",
    "molecular_ion": "polyatomic_ion",
    "material": "inorganic_crystal",
}
MIXTURE_TYPE_RENAMES = {
    "liquid mix": "liquid_mix",
    "gas mix": "gas_mix",
    "solid mix": "solid_mix",
    "reaction_mixture": "reaction_mix",
    "defined_mix": "other",
}


def rename_type_values(apps, schema_editor):
    Substance = apps.get_model("inventory_management", "Substance")
    Mixture = apps.get_model("inventory_management", "Mixture")

    # changed substances are marked as unsynced so the datastore picks them up
    for old, new in SUBSTANCE_TYPE_RENAMES.items():
        Substance.objects.filter(substance_type=old).update(
            substance_type=new,
            datastore_synced_at=None,
        )
    Substance.objects.filter(substance_type="unknown").update(
        substance_type=None,
        is_unknown=True,
        datastore_synced_at=None,
    )

    for old, new in MIXTURE_TYPE_RENAMES.items():
        Mixture.objects.filter(mixture_type=old).update(mixture_type=new)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory_management", "0010_substance_datastore_synced_at"),
    ]

    operations = [
        # Django can't add a `through` model to an existing many-to-many
        # field, so the existing link table is adopted as `MixtureComponent`
        # without changing the database. Extra columns are added after.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="MixtureComponent",
                    fields=[
                        ("id", models.AutoField(primary_key=True, serialize=False)),
                        (
                            "mixture",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="components",
                                to="inventory_management.mixture",
                            ),
                        ),
                        (
                            "substance",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="mixture_components",
                                to="inventory_management.substance",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "inventory_management__mixture_components",
                        "unique_together": {("mixture", "substance")},
                    },
                    bases=(models.Model, simmate.database.core.archive.ArchiveMixin),
                ),
                migrations.AlterField(
                    model_name="mixture",
                    name="substances",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="mixtures",
                        through="inventory_management.MixtureComponent",
                        to="inventory_management.substance",
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.AddField(
            model_name="mixturecomponent",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="mixturecomponent",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="mixturecomponent",
            name="role",
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name="mixturecomponent",
            name="amount",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mixturecomponent",
            name="amount_units",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name="substance",
            name="substance_type",
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.RunPython(rename_type_values, migrations.RunPython.noop),
    ]
