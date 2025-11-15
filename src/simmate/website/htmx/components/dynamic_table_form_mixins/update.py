# -*- coding: utf-8 -*-


class UpdateMixin:

    # for form_mode "update"

    ignore_on_update: list[str] = []
    """
    List of columns/fields to ignore when the form_mode = "update"
    """

    @property
    def mount_for_update_columns(self) -> list:
        """
        Columns that (in order!) should be mounted when preparing for an update.
        By default, this is all columns of the table other than id, created_at,
        and updated_at
        """
        exclude = [
            "id",
            "created_at",
            "updated_at",
        ]
        return [
            c for c in self.table.get_column_names(id_mode=True) if c not in exclude
        ]

    def mount_for_update(self):
        # This section is entered when we have many_to_one child components.
        # if self.is_subform:
        #     if not self.parent or not self.uuid:
        #         raise Exception("A UUID and parent component are required")
        #     # the parent component is in update mode, but this still might be a
        #     # new reagent (meaning it should be create mode)
        #     # we therefore use the uuid to see check if its a new entry
        #     # catch if this should actually be a create method, so we pivot
        #     if not self.table.objects.filter(uuid=self.uuid).exists():
        #         self.form_mode = "create"
        #         self.mount_for_create()
        #         return
        #     # otherwise, we do in fact have an update, and can grab the existing
        #     # object using the uuid
        #     self.table_entry = self.table.objects.get(uuid=self.uuid)
        #     # defaults
        #     self.is_editting = False
        #     self.is_confirmed = True
        #     self.redirect_mode = "no_redirect"
        # # This section is entered on typical behavior -- it is the main component
        # # and the ID is pulled from the url
        # else:

        # we pull the entry ID from the URL
        view_kwargs = self.request.resolver_match.kwargs
        self.table_entry = self.table.objects.get(id=view_kwargs["table_entry_id"])

        # With the table_entry set above, we can now set initial data using the
        # database and applying its values to the form fields.
        for field in self.mount_for_update_columns:
            current_val = getattr(self.table_entry, field)
            self.update_form(field, current_val)

        # SPECIAL CASES
        # TODO: support other
        # if "tags" in self.mount_for_update_columns
        if hasattr(self.table_entry, "tags"):
            tag_ids = list(self.table_entry.tags.values_list("id", flat=True).all())
            self.update_form("tag_ids", tag_ids)

    def check_form_for_update(self):
        self.check_form_for_create()  # default is to repeat create checks

    def unmount_for_update(self):
        # maybe use self.table_entry.update_from_toolkit()?
        for field, value in self.form_data.items():
            if field in self.ignore_on_update:
                # skip things like "molecule" and "molecule_original" that are
                # present for creation but should be ignored here
                continue
            setattr(self.table_entry, field, value)

    def save_to_db_for_update(self):
        self.save_to_db_for_create()  # default is to repeat create method
