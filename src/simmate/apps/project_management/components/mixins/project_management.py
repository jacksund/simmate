# -*- coding: utf-8 -*-

from simmate.website.utilities import parse_multiselect

from ...models import Project, Tag
from .project import ProjectInput


class ProjectManagementInput(ProjectInput):

    class Meta:
        javascript_exclude = (*ProjectInput.Meta.javascript_exclude,)

    search_inputs = [
        "project_id",
        # "tag_ids",
        "hypothesis_id",
    ]

    # -------------------------------------------------------------------------

    # project_id = None --> inheritted
    # project_options --> inheritted

    project__display = None
    _project_obj = None

    def set_project_id(self, project_id):
        self.project_id = project_id
        self.project_obj = Project.objects.get(id=self.project_id)

        self.tag_options = self.get_tag_options(self.project_obj)
        self.hypothesis_options = self.get_hypothesis_options(self.project_obj)

        self.call("refresh_select2")

        # populate display value for bulk form
        for p_id, p_name in self.project_options:
            if p_id == project_id:
                self.project__display = p_name
                break

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

    @staticmethod
    def get_hypothesis_options(project: Project) -> list[tuple]:

        # query for all tags
        tags = project.hypotheses.order_by("name").values_list("id", "name").all()

        # reformat into tuple of (value, display)
        return [(id, name) for id, name in tags]

    # -------------------------------------------------------------------------

    hypothesis_id = None
    hypothesis__display = None
    hypothesis_options = None  # set using Project.hypothesis_options

    def set_hypothesis_id(self, hypothesis_id):
        self.hypothesis_id = hypothesis_id
        if hypothesis_id is None:
            return

        # populate display value for bulk form
        for h_id, h_name in self.hypothesis_options:
            if h_id == hypothesis_id:
                self.hypothesis__display = h_name
                break

    # -------------------------------------------------------------------------

    tag_ids = None
    tags__display = None
    tag_options = []  # set dynamically using Project.tag_options

    def set_tag_ids(self, tag_ids):
        self.tag_ids = parse_multiselect(tag_ids)
        if tag_ids is None:
            return

        # populate display value for bulk form
        self.tags__display = ""
        for tag_id in self.tag_ids:
            for t_id, t_name in self.tag_options:
                if t_id == tag_id:
                    self.tags__display += f"{t_name}; "
                    break

    # -------------------------------------------------------------------------
