# -*- coding: utf-8 -*-

from simmate.website.htmx.components import HtmxComponent

from ..models import PricedItem


class PricedItemsReport(HtmxComponent):

    template_name = "price_catalog/priced_items/report.html"

    item_names_options: list[str] = None  # set in mount
    # years_ago_norm_options: list[int] = PricedItem.years_ago_options

    years_ago_norm_options = [
        (1, "Δ1y"),
        (5, "Δ5y"),
        (10, "Δ10y"),
        (25, "Δ25y"),
        ("max", "Max"),
    ]

    def mount(self):

        self.priced_item_id = self.request.resolver_match.kwargs["table_entry_id"]
        self.priced_item = PricedItem.objects.get(id=self.priced_item_id)

        self.item_names_options = list(
            PricedItem.objects.values_list("name", flat=True).order_by("name").all()
        )
        self.form_data = {
            "item_names": [],  # ["S&P 500", "Gold"]
            "use_percent": False,
            "use_inflation_adj": False,
            "years_ago_norm": "max",
        }
        self.process()  # to create figure

    def post_parse(self):
        # BUG: checkbox field does not show in POST data when =False. This is
        # normal HTML behavior to save on bandwidth, but causes a bug here.
        if "use_percent" not in self.post_data.keys():
            self.post_data["use_percent"] = False
        if "use_inflation_adj" not in self.post_data.keys():
            self.post_data["use_inflation_adj"] = False

    def process(self):

        if self.form_data["item_names"]:
            self.figure = PricedItem.get_report_figure(
                names=[self.priced_item.name] + self.form_data["item_names"],
                years_ago_norm=(
                    self.form_data["years_ago_norm"]
                    if self.form_data["years_ago_norm"] != "max"
                    else None
                ),
                percent=(
                    self.form_data["use_percent"]
                    if self.form_data["years_ago_norm"] != "max"
                    else None
                ),
                inflation_adj=self.form_data["use_inflation_adj"],
            )

        elif self.form_data["years_ago_norm"] == "max":
            self.figure = self.priced_item.get_price_figure(
                inflation_adj=self.form_data["use_inflation_adj"],
            )

        else:
            self.figure = self.priced_item.get_delta_figure(
                years_ago=self.form_data["years_ago_norm"],
                percent=self.form_data["use_percent"],
                inflation_adj=self.form_data["use_inflation_adj"],
            )

    # -------------------------------------------------------------------------

    def on_change_hook__item_names(self):
        # bug-fix: when only one is selected, the value isn't put in a list
        if isinstance(self.form_data["item_names"], str):
            self.form_data["item_names"] = [self.form_data["item_names"]]

    def on_change_hook__years_ago_norm(self):
        if self.form_data["years_ago_norm"] != "max":
            self.form_data["item_names"] = []
            # self.form_data["use_percent"] = True
            # self.form_data["use_inflation_adj"] = True
