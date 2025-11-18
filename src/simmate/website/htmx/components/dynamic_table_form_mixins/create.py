# -*- coding: utf-8 -*-

from django.db import transaction


class CreateMixin:

    # for form_mode "create"

    required_inputs: list[str] = []
    """
    For update and create form modes, these are the list of attributes that must
    be completed, otherwise the form will not submit.
    """

    table_entry = None

    # for to_many fields (tag_ids, user_ids, etc)
    table_entry_to_many_data: dict = {}

    _db_save_completed: bool = False

    def mount_for_create(self):
        return  # default is there's nothing extra to do

    def check_form_for_create(self):
        self.check_required_inputs()

    def unmount_for_create(self):
        direct_data = {}
        to_many_data = {}  # e.g., "tags__ids" or "users__ids"
        for key, value in self.form_data.items():
            if key.endswith("__ids"):
                to_many_data[key[:-5]] = value
            else:
                direct_data[key] = value

        self.table_entry = self.table.from_toolkit(**direct_data)
        self.table_entry_to_many_data = to_many_data

    def save_to_db_for_create(self):

        # BUG: race condition if user double-clicks button, triggering 2 calls to
        # the 'submit_form' method, which can create multiple instances of the
        # same entry.
        # Soluton 1:
        #   https://stackoverflow.com/questions/16715075/
        # Solution 2:
        # to prevent duplicates from being made, we need this to be update_or_create
        # inchi_key = config["molecule"].to_inchi_key()
        # self.table.objects.update_or_create(
        #     inchi_key=inchi_key,
        #     defaults=self.table.from_toolkit(
        #         as_dict=True,
        #         **self.form_data,
        #     ),
        # )
        if self._db_save_completed:
            # might be a duplicate call so we exit
            raise Exception(
                "This object was already saved. You might have a race condition."
            )
        self._db_save_completed = True

        with transaction.atomic():
            self.table_entry.save()

            # handle to_many data (such as tag_ids)
            for relation_name, ids_list in self.table_entry_to_many_data.items():
                if not hasattr(self.table_entry, relation_name):
                    raise Exception(
                        f"To-many relation data given with '{relation_name}__ids'"
                        f" but model has no relation named '{relation_name}'"
                    )
                relation = getattr(self.table_entry, relation_name)
                if not ids_list:
                    relation.clear()  # allows unsetting on updates
                else:
                    relation.set(ids_list)
