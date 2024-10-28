# -*- coding: utf-8 -*-

from django.shortcuts import redirect
from django_unicorn.components import UnicornView

from simmate.database.base_data_types import DatabaseTable


class DynamicFormComponent(UnicornView):
    """
    The abstract base class for dynamic front-end views.
    """

    template_name: str = None
    """
    The location of the template to use for this component
    """
    # TODO: Could there be a template that auto builds the form html? But this
    # might get messy and not be worth it.

    class Meta:
        javascript_exclude = (
            "page_title",
            "breadcrumbs",
            "breadcrumb_active",
            "required_fields",
        )

    # -------------------------------------------------------------------------

    # Options for UI elements
    # Only used in full-page views

    page_title: str = "The Bulk Synthesis App"
    """
    Title of the page (top left of page)
    """

    breadcrumbs: list = [
        ("apps", "Apps"),
    ]
    """
    List of breadcrumb links (top right of page)
    """

    breadcrumb_active: str = "Dynamic Form"
    """
    The active breadcrumb (top right of page)
    """

    # -------------------------------------------------------------------------

    def set_property(
        self,
        # BUG: for some reason, giving ": str" causes errors...?
        property_name: any,
        new_value: any,
        *args,
        **kwargs,
    ):
        # check if there is a special defined method for this property
        method_name = f"set_{property_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(new_value, *args, **kwargs)
        else:
            setattr(self, property_name, new_value)

    # -------------------------------------------------------------------------

    # Model creation and update utils

    table_entry: DatabaseTable = None  # initialized object
    table: DatabaseTable = None  # class object

    def get_config(self):
        pass  # TODO

    def mount_for_update(self):
        pass  # TODO

    def unmount_for_save(self):
        pass  # TODO

    # -------------------------------------------------------------------------

    # Basic form validation utils

    required_inputs: list[str] = []
    """
    For submission forms, these are the list of attributes that must be
    completed, otherwise the form will not submit.
    """

    def check_required_inputs(self):
        # Check that all basic inputs are filled out
        for input_name in self.required_inputs:
            input_value = getattr(self, input_name)
            if not input_value:
                message = f"'{input_value}' is a required input."
                self.errors.append(message)

    # -------------------------------------------------------------------------

    # Validation Hooks

    errors = []

    def check_form(self) -> bool:

        # reset errors for this new check
        self.errors = []

        # Check that all basic inputs are filled out
        self.check_required_inputs()

        # Call extra hook in case subclass defines its own checks
        self.check_form_hook()

        return True if not self.errors else False

    def check_form_hook(self) -> bool:
        return True  # default is there's nothing extra to check

    # -------------------------------------------------------------------------

    # Submission Hooks

    def submit_form(self):

        # check form is valid
        if not self.check_form():
            return

        self.presave_to_db_hook()
        self.save_to_db_hook()
        self.postsave_to_db_hook()

        return redirect(
            "data_explorer:table",
            self.table.table_name,
        )

    def presave_to_db_hook(self):
        return  # default is there's nothing extra to do

    def save_to_db_hook(self):
        return  # default is there's nothing extra to do

    def postsave_to_db_hook(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------
