# -*- coding: utf-8 -*-

from simmate.workflow_engine import task, Workflow


@task
def run_customized_s3task(
    workflow_base: Workflow,
    input_parameters: dict,
    updated_settings: dict,
):

    # ensure this workflow has a S3Task class attribute
    if not hasattr(workflow_base, "s3task"):
        raise Exception(
            "Dynamically updating settings is only supported for workflows "
            "generated via the `s3task_to_workflow` utility."
        )

    # we can't just copy the workflow and update attributes, as this will update
    # attributes of source workflow as well. Instead, we must subclass the underlying
    # tasks and then update their attributes. Therefore, this process below seeks
    # to copy and update relevant attributes before subclassing at the end.
    #   see https://stackoverflow.com/questions/9541025/

    # we start with the original s3task class and keep track of attributes we
    # need to update.
    s3task = workflow_base.s3task
    final_attributes = {}

    # Key will be something like "incar" and the update_values will be a
    # dictionary such as {"ENCUT": 520, "NPAR": 3}
    for update_attribute, update_values in updated_settings.items():

        original_config = getattr(s3task, update_attribute)

        # we will be deleting/editting the dictionary so we need to make a copy
        new_config = original_config.copy()

        # If a user sets EDIFF = 1e-3 and there is EDIFF__per_atom in the
        # incar dictionary, we need to remove that key as well. We therefore
        # remove all other "examplekey__*" settings from the dictionary.
        for update_key in update_values.keys():
            for subkey in original_config.keys():
                if subkey.startswith(f"{update_key}__"):
                    new_config.pop(subkey)
        # BUG: what about keywords like multiple_keywords__smart_ldau? I may need
        # to refactor the INCAR class to handle this.

        # now we can add the custom values
        new_config.update(update_values)

        final_attributes[update_attribute] = new_config

    # Dynamically create a subclass of the original s3task
    NewS3Task = type(f"Custom{s3task.__name__}", (s3task,), final_attributes)

    # now run the task with the remaining parameters
    # Note, we are using run_config instead of run because we do not want this
    # registered as a task run of the original class
    result = NewS3Task.run_config(**input_parameters)

    return result
