# -*- coding: utf-8 -*-


class CreateManyMixin:

    # for form_mode "create_many"

    applied_create_many_defaults: bool = False
    apply_to_children_inputs: list = []

    entries_for_create_many: list = []  # ie child_components
    parent_component = None

    def mount_for_create_many(self):
        self.redirect_mode = "table"

    def check_form_for_create_many(self):
        for child in self.children:
            if not child.check_form():
                for error in child.form_errors:
                    if error not in self.form_errors:
                        self.form_errors.append(error)

    def unmount_for_create_many(self):
        for child in self.children:
            child.unmount_for_create()

    def save_to_db_for_create_many(self):
        for child in self.children:
            child.presave_to_db()
            child.save_to_db()
            child.postsave_to_db()

    def save_to_db_for_create_many_entry(self):
        self.save_to_db_for_create()  # default is to repeat create method

    def apply_to_children(self):

        # BUG-FIX: see https://github.com/adamghill/django-unicorn/issues/666
        # Applying to children only works when is_editting is disabled
        for child in self.children:
            child.is_editting = False

        for form_attr in self.apply_to_children_inputs:
            parent_val = getattr(self, form_attr)
            if parent_val is None:
                continue
            for child in self.children:
                child.set_property(form_attr, parent_val)

        self.applied_create_many_defaults = True

    # -------------------------------------------------------------------------

    is_editting: bool = False

    def toggle_is_editting(self):
        self.is_editting = not self.is_editting
        if self.is_editting:
            self.js_actions = [
                {"refresh_select2": []},
            ]

    # -------------------------------------------------------------------------

    # TODO

    # for many_to_one type child components

    # is_subform: bool = False
    # subform_pointer: str = None  # e.g. parent_id

    # # is_editting: bool = True  ( this is set in create_many section ^^^)
    # uuid: str = None
    # is_confirmed: bool = False
