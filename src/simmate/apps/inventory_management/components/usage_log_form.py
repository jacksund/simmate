# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import UsageLog


class UsageLogForm(DynamicTableForm):
    table = UsageLog

    html_display_name = "Containers Usage Logs"
    html_description_short = (
        "Instances where a user interacts with a container, such as removing "
        "some material for an experiment."
    )
