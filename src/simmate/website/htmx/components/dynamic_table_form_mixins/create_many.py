# -*- coding: utf-8 -*-


class CreateManyMixin:

    # for form_mode "create_many"

    def mount_for_create_many(self):
        self.redirect_mode = "table"

    def check_form_for_create_many(self):
        for child in self.child_components:
            if not child.check_form():
                for error in child.form_errors:
                    if error not in self.form_errors:
                        self.form_errors.append(error)

    def unmount_for_create_many(self):
        for child in self.child_components:
            child.unmount_for_create()

    def save_to_db_for_create_many(self):
        for child in self.child_components:
            child.presave_to_db()
            child.save_to_db()
            child.postsave_to_db()

    # -------------------------------------------------------------------------

    child_components: list = None  # ie individual entries for the create many
    parent_component = None

    applied_defaults_to_children: bool = False
    ignore_on_apply_to_children: list = []

    def create_child_component(self):
        child = self.__class__(
            context=self.initial_context,  # or should it be the current context?
            form_mode="create_many_entry",
        )

        # linking them together -- for forward and reverse access
        if self.child_components is None:
            self.child_components = []  # first child needs new list
        self.child_components.append(child)
        child.parent_component = self

        return child

    def apply_to_children(self):

        for key, value in self.form_data.items():
            if value is None:
                continue

            for child in self.child_components:
                # OPTIMIZE: what if the hooks are slow and should be avoided?
                child.update_form(key, value)

        # tags special case -- it isn't applied by default bc it is an attribute
        if hasattr(self, "tag_ids") and self.tag_ids is not None:
            for child in self.child_components:
                # OPTIMIZE: what if the hooks are slow and should be avoided?
                child.update_form("tag_ids", self.tag_ids)

        self.applied_defaults_to_children = True

    # -------------------------------------------------------------------------

    is_editting: bool = False

    def toggle_is_editting(self):
        self.is_editting = not self.is_editting
        if self.is_editting:
            self.js_actions = [
                {"refresh_select2": []},
            ]

    # -------------------------------------------------------------------------
