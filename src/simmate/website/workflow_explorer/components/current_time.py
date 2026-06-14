# -*- coding: utf-8 -*-

from django.utils import timezone

from simmate.website.htmx.components.base import HtmxComponent


class CurrentTimeComponent(HtmxComponent):

    template_name: str = "workflow_explorer/current_time.html"

    @property
    def current_time(self):
        return timezone.now()
