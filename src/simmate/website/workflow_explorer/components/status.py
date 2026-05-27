# -*- coding: utf-8 -*-

from simmate.website.htmx.components.base import HtmxComponent


class WorkflowStatusComponent(HtmxComponent):

    template_name: str = "workflow_explorer/status.html"

    table_entry = None

    @property
    def current_status(self):
        if self.table_entry:
            self.table_entry.refresh_from_db()
            return self.table_entry.status
        return None
