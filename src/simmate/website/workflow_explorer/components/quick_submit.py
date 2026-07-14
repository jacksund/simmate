# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.website.htmx.components import HtmxComponent, MoleculeInput, StructureInput
from simmate.workflows.utils import get_workflow


class QuickSubmitComponent(HtmxComponent, StructureInput, MoleculeInput):
    """
    A guided workflow submission component for beginners and experts.
    """

    template_name = "workflow_explorer/quick_submit.html"

    post_data_mappings = {
        "calculation_types": list[str],
    }

    # State variables
    is_submission_confirmed: bool = False
    statuses: list = None

    # Step 1: Input Type Selection
    primary_input_type_options = [
        ("structure", "Crystal Structure"),
        ("molecule", "Molecule"),
        ("composition", "Composition"),
    ]

    # Workflow Mappings
    WORKFLOW_MAPPINGS = {
        "structure": {
            "Static Energy": "static-energy.quantum-espresso.quality00",
            "Relaxation": "relaxation.quantum-espresso.quality00",
            "Population Analysis": "population-analysis.vasp.elf-matproj",
            "DOS & Band-Structure": "band-structure.vasp.matproj",
            "Diffusion": "diffusion.vasp.neb-all-paths-mit",
            "Molecular Dynamics": "dynamics.vasp.mit",
        },
        "composition": {
            "Fixed-Composition Search": "structure-prediction.toolkit.fixed-composition",
            "Chemical System Search": "structure-prediction.toolkit.chemical-system",
        },
    }

    # Step 3: Calculation Type Selection (dynamically generated based on Step 1)
    @property
    def calculation_type_options(self):
        input_type = self.form_data.get("primary_input_type")
        mappings = self.WORKFLOW_MAPPINGS.get(input_type, {})
        return [(k, k) for k in mappings.keys()]

    @property
    def primary_input_label(self) -> str:
        """Label to display for the selected input type."""
        mapping = dict(self.primary_input_type_options)
        input_type = self.form_data.get("primary_input_type")
        return mapping.get(input_type, "")

    @property
    def primary_input_icon(self) -> str:
        """Icon to display for the selected input type."""
        mapping = {
            "structure": "bi-boxes",
            "molecule": "bi-hexagon-fill",
            "composition": "bi-funnel",
        }
        input_type = self.form_data.get("primary_input_type")
        return mapping.get(input_type, "")

    # -------------------------------------------------------------------------
    # Hooks to handle dynamic updates
    # -------------------------------------------------------------------------

    def on_change_hook__primary_input_type(self):
        """Reset the calculation types whenever the user changes the input type."""
        self.form_data["calculation_types"] = []

    def on_change_hook__structure__file(self):
        self.load_structure("structure")

    def on_change_hook__structure__database_id(self):
        self.load_structure("structure")

    def on_change_hook__molecule__molecule_text(self):
        self.load_molecule("molecule")

    def on_change_hook__molecule__molecule_sketcher(self):
        self.load_molecule("molecule")

    # -------------------------------------------------------------------------
    # Submission Logic
    # -------------------------------------------------------------------------

    def get_workflow_name(self, input_type: str, calc_type: str) -> str:
        """Map the user's choices to a specific workflow name."""
        return self.WORKFLOW_MAPPINGS.get(input_type, {}).get(calc_type)

    def submit_workflow(self, **kwargs):
        input_type = self.form_data.get("primary_input_type")
        calc_types = self.form_data.get("calculation_types", [])

        if not calc_types:
            return

        self.statuses = []
        for calc_type in calc_types:
            workflow_name = self.get_workflow_name(input_type, calc_type)
            if not workflow_name:
                continue

            workflow = get_workflow(workflow_name)

            # Prepare parameters
            parameters = {}
            if input_type and input_type in self.form_data:
                parameters[input_type] = self.form_data[input_type]

            # Filter to only allowed parameters
            allowed_parameters = workflow.parameter_names
            cleaned_parameters = {
                k: v for k, v in parameters.items() if k in allowed_parameters
            }

            if (
                hasattr(self, "request")
                and self.request
                and self.request.user.is_authenticated
                and "submitted_by_id" in allowed_parameters
            ):
                cleaned_parameters["submitted_by_id"] = self.request.user.id

            # Run cloud submission
            status = workflow.run_cloud(**cleaned_parameters)
            # monkey-patch workflow_name for UI display
            status.workflow_name_display = calc_type
            self.statuses.append(status)

        self.is_submission_confirmed = True

    def clear_input_type(self, **kwargs):
        """Reset the form data so the user can select a new input type without page reload."""
        self.reset_form()
        # no return value means it re-renders the component template automatically

    def reset_form(self, **kwargs):
        """Reset the submission process without reloading the page."""
        self.form_data = {}
        self.is_submission_confirmed = False
        self.statuses = None
