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
        By default, this is all keys output by the to_db_dict method, in no
        particular order.
        """
        # This is rarely overwritten and only ever used within mount_for_update.
        # We allow it to be overwritten because sometimes the order in
        # which cols are listed here is important (e.g. col1 and its set_col1
        # method MUST be called before col2 and set_col2)
        return list(self.to_db_dict(include_empties=True).keys())

    def mount_for_update(self):
        raise NotImplementedError("mount_for_update")
        # This section is entered when we have many_to_one child components.
        if self.is_subform:
            if not self.parent or not self.uuid:
                raise Exception("A UUID and parent component are required")

            # the parent component is in update mode, but this still might be a
            # new reagent (meaning it should be create mode)
            # we therefore use the uuid to see check if its a new entry

            # catch if this should actually be a create method, so we pivot
            if not self.table.objects.filter(uuid=self.uuid).exists():
                self.form_mode = "create"
                self.mount_for_create()
                return

            # otherwise, we do in fact have an update, and can grab the existing
            # object using the uuid
            self.table_entry = self.table.objects.get(uuid=self.uuid)

            # defaults
            self.is_editting = False
            self.is_confirmed = True
            self.redirect_mode = "no_redirect"

        # This section is entered on typical behavior -- it is the main component
        # and the ID is pulled from the url
        else:
            view_kwargs = self.request.resolver_match.kwargs
            self.table_entry = self.table.objects.get(id=view_kwargs["table_entry_id"])

        # With the table_entry set above, we can now set initial data using the
        # database and applying its values to the form fields.
        for field in self.mount_for_update_columns:
            current_val = getattr(self.table_entry, field)
            self.set_property(field, current_val)

        # SPECIAL CASES
        # TODO: support other m2m
        if hasattr(self, "tag_ids") and hasattr(self.table_entry, "tags"):
            self.tag_ids = list(
                self.table_entry.tags.values_list("id", flat=True).all()
            )

    def check_form_for_update(self):
        self.check_form_for_create()  # default is to repeat create checks

    def unmount_for_update(self):
        # set initial data using the form fields and applying its values to
        # the table entry (this is the reverse of mount_for_update)
        config = self.to_db_dict(include_empties=True)
        for field in config:
            if not hasattr(self, field) or field in self.ignore_on_update:
                # skip things like "molecule" and "molecule_original" that are
                # present for creation but should be ignored here
                continue
            current_val = getattr(self, field)
            setattr(self.table_entry, field, current_val)

    def save_to_db_for_update(self):
        self.save_to_db_for_create()  # default is to repeat create method
