# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.website.htmx.components import HtmxComponent
from simmate.workflows.utilities import get_all_workflows


class WorkflowSearchForm(HtmxComponent):

    template_name = "workflows/search_form.html"

    tags_options: list[str] = None  # set in mount()

    def mount(self):
        self.workflows = [w for w in get_all_workflows() if not w.is_hidden]
        self.nworkflows = len(self.workflows)
        self.tags_options = list(
            {
                t
                for w in self.workflows
                for t in w.tags
                if t != "simmate" and t != w.name_full
            }
        )
        self.tags_options.sort()
        self.form_data["recommended_only"] = True
        self.form_data["order_by"] = ["name_type", "name_app", "name_preset"]
        self.process()

    def post_parse(self):
        # BUG: checkbox field does not show in POST data when =False. This is
        # normal HTML behavior to save on bandwidth, but causes a bug here.
        if "recommended_only" not in self.post_data.keys():
            self.post_data["recommended_only"] = False

    def process(self):
        rec_only = self.form_data.get("recommended_only")
        selected_tags = set(self.form_data.get("tags", []))
        selected_order_by = self.form_data.get("order_by", [])

        # 1. Filter by recommendation status
        workflows = [w for w in self.workflows if not rec_only or w.is_recommended]

        # 2. Filter by tags (if any tags were provided)
        if selected_tags:
            workflows = [w for w in workflows if selected_tags.intersection(w.tags)]

        self.workflows_show = workflows
        self.nworkflows_show = len(self.workflows_show)

        # Sort workflows by requested column(s)
        if selected_order_by:
            for key in reversed(selected_order_by):

                default_val = (
                    ""
                    if key.strip("-") in ["name_preset", "name_app", "name_type"]
                    else 0
                )

                self.workflows_show.sort(
                    key=lambda s: getattr(s, key.strip("-")) or default_val,
                    reverse=key.startswith("-"),
                )
            # self.workflows_show.sort(
            #     key=lambda s: [getattr(s, k) for k in selected_order_by], reverse=True
            # )

    def submit(self):
        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)

    # -------------------------------------------------------------------------

    def set_order_by(self, order_by_value: str):
        current_order_by = self.form_data["order_by"]

        # I allow up to 3 ordering tags and also reset all ordering when
        # a column is repeated
        if (
            order_by_value in current_order_by
            or order_by_value.strip("-") in current_order_by
        ):
            self.form_data["order_by"] = [order_by_value]
        elif len(current_order_by) >= 3:
            self.form_data["order_by"].insert(0, order_by_value)
            self.form_data["order_by"] = self.form_data["order_by"][:2]
        else:
            self.form_data["order_by"].insert(0, order_by_value)

        self.process()

    def on_change_hook__tags(self):
        # bug-fix: when only one is selected, the value isn't put in a list
        if isinstance(self.form_data["tags"], str):
            self.form_data["tags"] = [self.form_data["tags"]]
