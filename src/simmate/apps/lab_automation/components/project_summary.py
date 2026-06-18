# -*- coding: utf-8 -*-

from simmate.website.htmx.components.base import HtmxComponent


class ProjectSummaryComponent(HtmxComponent):
    template_name: str = "lab_automation/components/project_summary.html"

    @property
    def ai_summary(self) -> str:
        return (
            "Current focus is on synthesizing high-purity YBa2Cu3O7 superconductor samples. "
            "Recent XRD results from Batch 11 indicate an optimal calcination profile, so the "
            "current task (Batch 12) is replicating those exact parameters. "
            "Hotplate 1 is currently pre-heating for the next synthesis step while "
            "Hotplate 2 performs calcination for Sample C. "
            "All environment sensors are nominal. Lab humidity is perfectly controlled at 35%."
        )

    @property
    def last_updated(self) -> str:
        return "Just now"
