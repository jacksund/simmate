# -*- coding: utf-8 -*-

from functools import cached_property

from ...models import Project


class ProjectInput:

    class Meta:
        javascript_exclude = ("project_options",)

    project_id = None

    @cached_property
    def project_options(self):
        projects = Project.objects.order_by("name").values_list("id", "name").all()
        return [(id, name) for id, name in projects]
