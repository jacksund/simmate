from django.db import migrations

# Substance used to have a FK column to each of these third-party datasets.
# The links now live on the dataset tables instead (many-to-one), and these
# columns were removed from 0002_initial. This drops them from databases that
# were created before that change, and does nothing on new databases.
REMOVED_COLUMNS = [
    "aflow_id",
    "bcpc_id",
    "cas_registry_id",
    "chembl_id",
    "chemspace_id",
    "cod_id",
    "emolecules_id",
    "enamine_id",
    "jarvis_id",
    "materials_project_id",
    "oqmd_id",
    "pdb_id",
    "ppdb_id",
]

TABLE = "inventory_management__substances"


def drop_removed_columns(apps, schema_editor):
    # Note: sqlite does not support "DROP COLUMN IF EXISTS", so we check
    # which columns are present first.
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing_columns = [
            column.name
            for column in connection.introspection.get_table_description(cursor, TABLE)
        ]
    for column in REMOVED_COLUMNS:
        if column in existing_columns:
            schema_editor.execute(
                f"ALTER TABLE {schema_editor.quote_name(TABLE)} "
                f"DROP COLUMN {schema_editor.quote_name(column)}"
            )


class Migration(migrations.Migration):
    dependencies = [
        (
            "inventory_management",
            "0007_rename_num_containers_batch_num_available_containers",
        ),
    ]

    operations = [
        migrations.RunPython(
            drop_removed_columns,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
