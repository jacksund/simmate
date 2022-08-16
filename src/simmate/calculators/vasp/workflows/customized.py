# -*- coding: utf-8 -*-

"""
# Example use

``` python
from simmate.workflows.customized import Customized__Vasp__UserConfig as workflow

result = workflow.run(
    workflow_base="relaxation.vasp.quality04",
    input_parameters={"structure": "NaCl.cif"},
    updated_settings={
        "incar": {"NPAR": 1, "ENCUT": 600},
    },
).result()
```

# Example input YAML

``` yaml
# Indicates we want to change the settings, using a specific workflow as a starting-point
workflow_name: vasp/customized
base_workflow: static-energy/mit

# These would update the class attributes for the single workflow run
# The "custom_" start indicates we are updating some attribute
custom_incar: 
    - ENCUT: 600
    - KPOINTS: 0.25
custom_potcar_mappings:
    - Y: Y_sv

# Then the remaining inputs are the same as the base_workflow
structure: POSCAR
command: mpirun -n 5 vasp_std > vasp.out
```
"""

import logging

from simmate.workflow_engine import S3Workflow, Workflow


class Customized__Vasp__UserConfig(Workflow):
    """
    "VASP calculation with updated INCAR/POTCAR settings
    """

    @staticmethod
    def run_config(
        workflow_base: Workflow,
        updated_settings: dict,
        input_parameters: dict,
        **kwargs,
    ):
        logging.warning(
            "WARNING: customized workflows are meant only for quick testing. "
            "If you are using custom settings regularly, we highly recommend "
            "making a new workflow inside a Simmate project instead. "
            "Read through tutorial 06 for more information."
        )

        # ensure this workflow has a S3Task class attribute
        if not issubclass(workflow_base, S3Workflow):
            raise Exception(
                "Dynamically updating settings is only supported for S3Workflows"
            )

        # we can't just copy the workflow and update attributes, as this will update
        # attributes of source workflow as well. Instead, we must subclass the
        # workflow and then update its attributes. Therefore, this process below seeks
        # to copy and update relevant attributes before subclassing at the end.
        #   see https://stackoverflow.com/questions/9541025/

        # we start with the original s3workflow class and keep track of
        # attributes we need to update.
        final_attributes = {}

        # Key will be something like "incar" and the update_values will be a
        # dictionary such as {"ENCUT": 520, "NPAR": 3}
        for update_attribute, update_values in updated_settings.items():

            original_config = getattr(workflow_base, update_attribute)

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

        # As an extra, we disable any registration & saving of results to the database
        final_attributes["use_database"] = False

        # Dynamically create a subclass of the original s3task
        NewWorkflow = type(
            f"{workflow_base.__name__}Custom", (workflow_base,), final_attributes
        )

        # now run the task with the remaining parameters
        # Note, we are using run_config instead of run because we do not want this
        # registered as a task run of the original class
        state = NewWorkflow.run(**input_parameters)
        result = state.result()

        return result
