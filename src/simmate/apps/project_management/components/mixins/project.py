# -*- coding: utf-8 -*-

from functools import cached_property

from ...models import Project, Tag


class ProjectInput:

    @cached_property
    def project_options(self):
        projects = Project.objects.order_by("name").values_list("id", "name").all()
        return [(id, name) for id, name in projects]

    @cached_property
    def tag_options(self):
        tags = Tag.objects.order_by("name").values_list("id", "name").all()
        return [(id, name) for id, name in tags]
