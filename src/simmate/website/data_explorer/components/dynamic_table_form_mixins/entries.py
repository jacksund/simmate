# -*- coding: utf-8 -*-


class EntriesMixin:

    page = None
    pagination_urls = None
    report = None
    total = None
    entries = None

    def mount_for_entries(self):
        if self.initial_context:
            self.page = self.initial_context.get("page")
            self.pagination_urls = self.initial_context.get("pagination_urls")
            self.report = self.initial_context.get("report")
            self.total = self.initial_context.get("total")
            self.entries = self.initial_context.get("entries")

            # if entries isn't explicitly provided, we fallback to the
            # page object list
            if self.entries is None and self.page is not None:
                self.entries = self.page.object_list
