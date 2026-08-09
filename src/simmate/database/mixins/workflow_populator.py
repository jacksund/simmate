# -*- coding: utf-8 -*-

import logging

from simmate.utils import chunk_list


class WorkflowPopulator:
    """
    A mix-in for database tables that adds functionality for populating
    columns using Simmate workflows (i.e. calculated columns).
    """

    workflow_columns: dict = {}
    """
    WARNING: advanced users only (this is still in early testing)
    
    When subclassing DatabaseTable, you may want to add a column that is 
    populated via a specific workflow (e.g. a quick property calculation). This
    attribute defines the mapping of a new column to a workflow name.
    
    You must define the column separately (as dynamically adding columns is not
    possible with Django models) and the workflow must be accessible with
    the `get_workflow` utility.
    
    Note, this is meant for bringing workflow results IN TO a table -- like
    having a full dataset (like the OQMD library) and wanting to add a column
    for some ML/AI model you've built. If your workflow takes >30s per entry,
    it is often better to build a separate workflow table to store results there.
    """

    @classmethod
    def populate_workflow_column(
        cls,
        column_name: str,
        batch_size: int = 500,
        update_only: bool = True,
        filters: dict = None,
    ):
        """
        Populates a specific workflow column. The column must be present in the
        `workflow_columns` attribute.
        """

        # BUG: using 'id__in' below might cause batches >1k to fail
        if batch_size > 1000:
            logging.info(
                "This method uses a 'IN' clause to select batches of IDs, so "
                "batches larger than 1k can cause performance issues and errors."
            )

        # local import to avoid circular dependency
        from simmate.workflows.utils import get_workflow

        # grab the workflow mapped to this column.
        # Config can be a simple string (single column) or a dict with
        # "workflow_name" and "columns" (multi-column from one workflow).
        column_config = cls.workflow_columns[column_name]
        if isinstance(column_config, dict):
            workflow_name = column_config["workflow_name"]
            # maps db_column_name -> result_key in the workflow output dict
            columns_mapping = column_config["columns"]
        else:
            workflow_name = column_config
            columns_mapping = None
        workflow = get_workflow(workflow_name)

        # BUG: I assume inputs are the common ones for now...
        # but I need a way to specify this for more diverse workflows
        # (I give one suggested fix to this in the while-loop below)
        if "molecules" not in workflow.parameter_names:
            raise Exception(
                "We are still at early stage testing for this method, so "
                "it only supports workflows that take 'molecules' as an "
                "input parameter. Reach out to our team if you'd like "
                "us to add additional support."
            )

        query_filters = {}
        if update_only:
            if columns_mapping:
                # filter where ALL of the mapped columns are null
                for db_col in columns_mapping:
                    query_filters[f"{db_col}__isnull"] = True
            else:
                query_filters[f"{column_name}__isnull"] = True
        # some tables allow "broken" entries, which we always want to skip
        if "is_invalid_molecule" in cls.get_column_names():
            query_filters["is_invalid_molecule"] = False
            query_filters["is_empty_molecule"] = False
        if "is_invalid_structure" in cls.get_column_names():
            query_filters["is_invalid_structure"] = False
        if filters:
            query_filters.update(filters)
        ids_to_update = (
            cls.objects.filter(**query_filters).values_list("id", flat=True).all()
        )

        logging.info(
            f"Updating '{column_name}' column using '{workflow_name}' "
            f"for {len(ids_to_update)} entries"
        )
        for ids_chunk in chunk_list(ids_to_update, batch_size):
            try:

                # grab the next set of objects to update
                objs_to_update = cls.objects.filter(id__in=ids_chunk).all()

                # First check for a user-defined method.
                predefined_method = f"_format_inputs_for__{column_name}"
                if hasattr(cls, predefined_method):
                    # method = getattr(cls, predefined_method)
                    # method(workflow, objs_to_update)
                    raise NotImplementedError("This feature is still being developed")
                else:
                    # BUG: see comment at start of for-loop where I say I assume
                    # a 'molecules' input
                    results = workflow.run(
                        molecules=objs_to_update.to_toolkit(),
                        compress_output=True,
                    )
                    logging.info("Saving results to db")
                    if columns_mapping:
                        # Multi-column workflow: results is a dict keyed
                        # by result_key, each value is a list of values
                        for db_col, result_key in columns_mapping.items():
                            for entry, val in zip(objs_to_update, results[result_key]):
                                setattr(entry, db_col, val)
                        cls.objects.bulk_update(
                            objs_to_update,
                            list(columns_mapping.keys()),
                        )
                    else:
                        for entry, entry_result in zip(objs_to_update, results):
                            setattr(entry, column_name, entry_result)
                        cls.objects.bulk_update(objs_to_update, [column_name])
            except:
                logging.warning("BATCH FAILED")
                continue

    @classmethod
    def populate_workflow_columns(cls, batch_size: int = 500):
        """
        Uses the `workflow_columns` property to fill columns with data.
        """
        for column_name in cls.workflow_columns.keys():
            cls.populate_workflow_column(column_name, batch_size=batch_size)
