# -*- coding: utf-8 -*-

import json


class UpdateManyMixin:

    # for form_mode "update_many"

    update_many_inputs: list[str] = []
    """
    List of columns/fields to allow when the form_mode = "update_many"
    """

    n_ids_to_update_max: int = 25
    """
    The max number of entries that can be editted at one time when
    form_mode = "update_many"
    """

    is_update_many_confirmed: bool = False
    """
    Whether the user accepted the warning that there is no undo button
    """

    entry_ids_to_update: list = []
    """
    The list of selected ids that will be updated. Only applies when the
    form_mode = "update_many"
    """

    def check_max_update_many(self):
        if len(self.entry_ids_to_update) > self.n_ids_to_update_max:
            message = f"You are only allowed to update a maximum of '{self.n_ids_to_update_max}' at a time."
            self.form_errors.append(message)

    def confirm_update_many(self, select_form_data):
        # Example of how the data will look:
        # {
        #     "example_select_all": "on",  # we want to ignore this
        #     "1": "on",
        #     "2": "on",
        #     "4": "on",
        #     "csrfmiddlewaretoken": "LTJaJf5gz6fUKUZaN0p6gMyVnLQGM7LGjPRVohe3pVgR5M0UpepNokgePN3pQ4dI"
        # }
        data = json.loads(select_form_data)
        data.pop("csrfmiddlewaretoken", None)
        self.entry_ids_to_update = [
            int(key) for key, value in data.items() if key.isnumeric()
        ]

        if self.entry_ids_to_update:
            self.is_update_many_confirmed = True

    def mount_for_update_many(self):
        # default is we want everything to be set to None, which includes
        # overriding default values
        for field in self.update_many_inputs:
            # opt for setattr instead of self.set_property since this is unsetting
            setattr(self, field, None)

    def unmount_for_update_many(self):
        config = self.to_db_dict()

        all_updates = {
            field: value
            for field, value in config.items()
            if field not in self.ignore_on_update and field in self.update_many_inputs
        }

        # Special cases! Comments should be appended so nothing is lost, whereas
        # flat updates replace the col value entirely.
        flat_updates = {}
        append_updates = {}
        for field, value in all_updates.items():
            if field == "comments" or field.endswith("_comments"):
                # TODO: allow other cols to be append type
                append_updates[field] = value
            else:
                flat_updates[field] = value

        self.final_updates = {
            "flat_updates": flat_updates,
            "append_updates": append_updates,
        }

    def save_to_db_for_update_many(self):

        flat_updates = self.final_updates["flat_updates"]
        append_updates = self.final_updates["append_updates"]

        # TODO: put this all within a single db transaction...?

        entries = self.table.objects.filter(id__in=self.entry_ids_to_update)

        # Note: bulk updating will cause a bug because it won't call `save()`
        # method (and therefore it will skip things like creating the history
        # entry). So we need to iterate the objects and save them one at a
        # time. This is slower + more sql calls, but UI updates are
        # typically limited  <50 entries so this should be fine.
        for entry in entries.all():
            for field, new_value in flat_updates.items():
                setattr(entry, field, new_value)
            for field, append_value in append_updates.items():
                current_value = getattr(entry, field)
                new_value = current_value + "\n\n" + append_value
                setattr(entry, field, new_value)
            entry.save()

            # SPECIAL CASE
            # TODO: support other m2m
            if hasattr(self, "tag_ids") and hasattr(entry, "tags") and self.tag_ids:
                # !!! for update many, do I want to set() or add()?
                entry.tags.add(*self.tag_ids)
                entry.save()
