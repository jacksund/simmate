# -*- coding: utf-8 -*-

from ...models import Project, Tag
from .project import ProjectInput


class ProjectManagementInput(ProjectInput):

    # -------------------------------------------------------------------------

    project__display = None

    def on_change_hook__project_id(self):

        project_id = self.form_data["project_id"]
        self.project_obj = Project.objects.get(id=project_id)

        self.tag_options = self.get_tag_options(self.project_obj)
        self.hypothesis_options = self.get_hypothesis_options(self.project_obj)

        self.js_actions = [
            {"refresh_select2": []},
        ]

        # populate display value for bulk form
        for p_id, p_name in self.project_options:
            if p_id == project_id:
                self.project__display = p_name
                break

    # -------------------------------------------------------------------------

    tag_options: list[tuple] = []  # set dynamically using Project.tag_options

    @staticmethod
    def get_tag_options(project: Project) -> list[tuple]:

        # query for all tags directly linked
        project_tags = project.tags.order_by("name").values_list("id", "name").all()

        # add in generic tags after specific ones
        generic_tags = (
            Tag.objects.filter(tag_type="all-projects")
            .order_by("name")
            .values_list("id", "name")
            .all()
        )

        # reformat into tuple of (value, display)
        return [
            (id, tag_name) for id, tag_name in list(project_tags) + list(generic_tags)
        ]

    tags__display = None

    def on_change_hook__tags__ids(self):
        # populate display value for bulk form
        tag_ids = self.form_data.get("tags__ids", [])
        self.tags__display = ""
        for tag_id in tag_ids:
            for t_id, t_name in self.tag_options:
                if t_id == tag_id:
                    self.tags__display += f"{t_name}; "
                    break

    # -------------------------------------------------------------------------

    hypothesis_options = None

    @staticmethod
    def get_hypothesis_options(project: Project) -> list[tuple]:

        # query for all tags
        tags = project.hypotheses.order_by("name").values_list("id", "name").all()

        # reformat into tuple of (value, display)
        return [(id, name) for id, name in tags]

    hypothesis__display = None

    def on_change_hook__hypothesis_id(self):
        hypothesis_id = self.form_data["hypothesis_id"]
        # populate display value for bulk form
        for h_id, h_name in self.hypothesis_options:
            if h_id == hypothesis_id:
                self.hypothesis__display = h_name
                break

    # -------------------------------------------------------------------------
