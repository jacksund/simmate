# -*- coding: utf-8 -*-


class ReportMixin:

    # Methods for reports and plotting.
    report_df_columns: list[str] = None

    def mount_for_report(self):
        return  # default is there's nothing extra to do

    @classmethod
    def get_report(cls, data_source=None) -> dict:

        # convert to a SearchResults/queryset obj
        if data_source == None:
            data_source = cls.table.objects  # use full table by default
        elif hasattr(data_source, "paginator"):  # checks if it's a Page object
            data_source = data_source.paginator.object_list

        columns = cls.report_df_columns
        df = data_source.to_dataframe(columns)

        # we prefer the method on the component, but fallback to the table
        if hasattr(cls, "get_report_from_df"):
            return cls.get_report_from_df(df)
        else:
            return {}
