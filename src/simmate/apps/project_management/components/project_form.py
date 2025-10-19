# -*- coding: utf-8 -*-

from django.db import transaction

from simmate.website.htmx.components import HtmxComponent

from ..models import Project

# DynamicTableForm, UserInput


class ProjectForm(HtmxComponent):

    table = Project

    template_name = "project_management/project/form.html"
    # template_names = dict(
    #     default="project_management/project/form.html",
    # )

    # -------------------------------------------------------------------------

    def suggest_new_name(self, request):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------

    required_inputs = [
        "name",
        "description",
        "discipline",
        "status",
        "leader_ids",
        "member_ids",
    ]
    search_inputs = [
        "name",
        "status",
        "discipline",
    ]

    def mount_for_update(self):
        super().mount_for_update()
        self.leader_ids = list(
            self.table_entry.leaders.values_list("id", flat=True).all()
        )
        self.member_ids = list(
            self.table_entry.members.values_list("id", flat=True).all()
        )

    def check_form_hook(self):

        # make sure the Project is a new one
        project_exists = False
        if self.form_mode == "create":
            project_exists = Project.objects.filter(name=self.name).exists()
        elif self.form_mode == "update":
            project_exists = (
                Project.objects.filter(name=self.name)
                .exclude(id=self.table_entry.id)
                .exists()
            )
        if project_exists:
            self.form_errors.append(
                f"A project with the name {self.name} already exists."
            )

    def save_to_db(self):

        if self.form_mode not in ["create", "update"]:
            return  # nothing to save

        # We are saving multiple objects (request + reagents), so we want to
        # make sure ALL work. If not, we roll back everything
        with transaction.atomic():

            # Save the request to the database
            self.table_entry.save()

            # add leaders and members
            self.table_entry.leaders.set(self.leader_ids)
            self.table_entry.members.set(self.member_ids)
            self.table_entry.save()

    def to_search_dict(self, **kwargs):
        search = self._get_default_search_dict(**kwargs)
        if self.leader_ids:
            search["leaders__id__in"] = self.leader_ids
        if self.member_ids:
            search["members__id__in"] = self.member_ids
        return search

    # -------------------------------------------------------------------------
