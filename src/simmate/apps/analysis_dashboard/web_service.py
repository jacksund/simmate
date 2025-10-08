from functools import reduce

import pandas as pd
import plotly.express as px
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from simmate.database import connect
from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule

from .plot_constructors.utilities import (
    get_plot_constructor,
    get_plot_constructor_options,
)

# -----------------------------------------------------------------------------

# utils

PX_DATA_MAPPING = {
    "Carshare": "carshare",
    "Election": "election",
    "Experiment": "experiment",
    "Gapminder": "gapminder",
    "Iris": "iris",
    "Medals Wide": "medals_wide",
    "Medals Long": "medals_long",
    "Stocks": "stocks",
    "Tips": "tips",
    "Wind": "wind",
}


def load_data():

    # first time loading
    if st.session_state.df is None:
        # bug check
        assert st.session_state.is_datasource_selected == True

        # Sample datasets
        if st.session_state.selected_dataset:
            # TODO: need to account for datasets NOT in px.data module
            mod_name = PX_DATA_MAPPING[st.session_state.selected_dataset]
            df = getattr(px.data, mod_name)()

        # Simmate URL
        if st.session_state.simmate_rest_url:
            queryset = DatabaseTable.filter_from_url(
                url=st.session_state.simmate_rest_url,
                paginate=False,
            )
            limit = 10_000
            size = queryset[:limit].count()
            if size >= limit:
                st.error(
                    body=(
                        "Your query is too large! Our dashboard is limited to "
                        "{limit} rows, but your query has {size}. Filter down your "
                        "queryset more before moving to the dashboard. Refresh "
                        "the page and try again"
                    ),
                    icon="🚨",
                )
                st.stop()
            if size == 0:
                st.error(
                    body=(
                        "Your query is empty! The URL gave back zero results. "
                        "Refresh the page and try again"
                    ),
                    icon="🚨",
                )
                st.stop()
            df = queryset.to_dataframe()

        # File upload
        elif st.session_state.uploaded_file:
            df = pd.read_csv(st.session_state.uploaded_file)

        # Testing scale limits -- this code duplicates df and makes it larger
        # df = pd.concat([df for n in range(10)])

        # we cache manually instead of using `@st.cache_data` because we may
        # modify the dataframe elsewhere (e.g. add new calculated columns)
        st.session_state.df = df

    # return the cached dataset (which might have modifications)
    return st.session_state.df


# -----------------------------------------------------------------------------

# Adjust the width of the Streamlit page
st.set_page_config(layout="wide")

# Set params that we track via session state (for speed-ups & logic below)
if "df" not in st.session_state:
    st.session_state.df = None

if "is_datasource_selected" not in st.session_state:
    st.session_state.is_datasource_selected = False

if "selected_dataset" not in st.session_state:
    st.session_state.selected_dataset = None
if "simmate_rest_url" not in st.session_state:
    st.session_state.simmate_rest_url = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


# -----------------------------------------------------------------------------

# Have user select/import dataset to analyze

if not st.session_state.is_datasource_selected:
    st.subheader("Please select a dataset to analyze")

    selected_dataset = st.selectbox(
        label="**Option 1: select a pre-configured dataset**",
        index=None,
        options=[
            # Demo datasets from plotly express
            *PX_DATA_MAPPING.keys()
            # Demo datasets from simmate
            #   (TODO)
            # Preconfigured datasets from simmate
            # "BLU22 Targets (DEV)",
        ],
    )
    if selected_dataset is not None:
        st.session_state.selected_dataset = selected_dataset
        st.session_state.is_datasource_selected = True
        st.rerun()

    simmate_rest_url = st.text_input(
        label="**Option 2: paste a Simmate URL**",
        placeholder="https://simmate.org/data/MaterialsProject/?id__lte=50",
    )
    if simmate_rest_url:
        st.session_state.simmate_rest_url = simmate_rest_url
        st.session_state.is_datasource_selected = True
        st.rerun()

    uploaded_file = st.file_uploader(
        label="**Option 3: upload your own CSV file**",
        type=["csv"],
        accept_multiple_files=False,
    )
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.is_datasource_selected = True
        st.rerun()

    # If we don't hit a rerun call above, we don't have a dataset yet
    st.stop()

# -----------------------------------------------------------------------------

# Once a dataset is selected, we can start analysis on it

df = load_data()

# create columns to put buttons in a row
column1, column2, column3, column4, column5 = st.columns(5)

with column1:
    with st.popover("Columns"):
        columns_display_toggles = [
            st.checkbox(
                label=column,
                value=True,
            )
            for column in df.columns
        ]
        columns_to_display = [
            column
            for display, column in zip(columns_display_toggles, df.columns)
            if display
        ]

with column2:
    with st.popover("Plot"):
        plot_type = st.selectbox(
            label="Plot Type",
            options=get_plot_constructor_options(),
            index=0,  # default to the chatbot!
        )
        plot_constructor = get_plot_constructor(plot_type) if plot_type else None
        plot_config = plot_constructor.get_inputs(df) if plot_type else {}

with column3:
    with st.popover("Filters"):

        # BUG: search as-is removes & resets filters not in search results
        # column_search_query = st.text_input("Search for column")
        # st.divider()

        filters = {}
        for column_name, column_dtype in zip(df.columns, df.dtypes):

            # if column_search_query and column_search_query not in column_name:
            #     continue

            # Code I wrote independently but also I later found this source,
            # which is almost exactly the same, so I used it tweak some checks:
            # https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/

            filter_value = None

            if column_dtype == dict:
                continue  # TODO: I don't build filters for json fields yet

            elif is_numeric_dtype(column_dtype):
                min_val = df[column_name].min()
                max_val = df[column_name].max()
                if min_val == max_val:
                    # this column only has a single value, so there is
                    # no need for a filter
                    continue
                default = (min_val, max_val)
                filter_value = st.slider(
                    column_name,
                    min_value=min_val,
                    max_value=max_val,
                    value=default,
                )
                if filter_value != default:
                    filters[column_name] = {
                        "metric": "range",  # aka between
                        "value": filter_value,
                    }
                # df = df[df[column].between(*user_num_input)]

            # Treat columns with < 10 unique values as categorical
            elif (
                isinstance(column_dtype, pd.CategoricalDtype)
                or df[column_name].nunique() < 10
            ):
                filter_value = st.multiselect(
                    label=column_name,
                    options=df[column_name].unique(),
                    default=None,
                )
                if filter_value:
                    filters[column_name] = {
                        "metric": "in",
                        "value": filter_value,
                    }
                    # df = df[df[column].isin(user_cat_input)]

            elif is_datetime64_any_dtype(column_dtype):
                continue  # TODO: I don't build filters for datetime fields yet
                # min_val = df[column_name].min()
                # max_val = df[column_name].max()
                # default = (min_val, max_val)
                # filter_value = st.date_input(
                #     column_name,
                #     value=default,
                # )
                # if filter_value != default:
                #     filters[column_name] = {
                #         "metric": "range",  # aka between
                #         "value": filter_value,
                #     }
                # if len(filter_value) == 2:
                #     user_date_input = tuple(map(pd.to_datetime, user_date_input))
                #     start_date, end_date = user_date_input
                #     df = df.loc[df[column].between(start_date, end_date)]

            else:
                filter_value = st.text_input(label=column_name)
                if filter_value:
                    filters[column_name] = {
                        "metric": "exact",  # !!! consider "contains"
                        "value": filter_value,
                    }
                # if filter_value:
                #     df = df[df[column].astype(str).str.contains(user_text_input)]

with column4:
    with st.popover("Add columns", disabled=True):
        smiles_column = st.selectbox(
            label="SMILES Column",
            options=df.columns,
            index=list(df.columns).index("smiles") if "smiles" in df.columns else None,
        )

        selected_x = st.multiselect(
            label="Calculated Properties",
            options=[
                "Molecular Weight",
                "2D Chemspace Mapping",
                "2D Similarity to",
            ],
            default=[],
        )

        st.divider()

        # TODO: add options for each one selected. E.g.m if 2D similarity,
        # add extra input option for smiles
        # TODO: actually apply these
        import time

        apply_calcs = st.button(
            "Apply",
            on_click=time.sleep,
            args=(2,),
            type="primary",
        )

with column5:
    st.download_button(
        label="Save / Share",
        data="{}",
        file_name="dashboard.json",
        mime="text/json",
        disabled=True,
    )


if filters:
    # build out checks by column and apply all of them to the df
    filter_conditions = []
    for column, filter_config in filters.items():
        metric = filter_config["metric"]
        value = filter_config["value"]
        if metric == "exact":
            check = df[column] == value
        elif metric == "range":
            check = df[column].between(*value)
        elif metric == "in":
            check = df[column].isin(value)
        else:
            raise Exception(f"Unknown filter metric: {metric}")
        filter_conditions.append(check)
    filtered_df = df[reduce(lambda x, y: x & y, filter_conditions)]
else:
    filtered_df = df

# default is empty dataframe in case section skipped below
selected_df = df[0:0]

if plot_constructor and plot_constructor.check_inputs(filtered_df, plot_config):
    with st.spinner("Generating Plot..."):
        fig = plot_constructor.get_plot(filtered_df, plot_config)

    # show table of points that are selected in the plot
    event = st.plotly_chart(fig, on_select="rerun")
    if event.selection:
        # BUG: these indicies are incorrect in some cases... Bug in streamlit?
        selected_points = list(event.selection.point_indices)
        if selected_points:
            selected_df = filtered_df[filtered_df.index.isin(selected_points)]

display_selected_only = st.checkbox(
    "Selected Only",
    value=False,  # show full table by default
)
display_df = (
    selected_df[columns_to_display]
    if display_selected_only
    else filtered_df[columns_to_display]
)

# Highlighting selected rows
# if not display_selected_only and len(selected_df) > 0:
#     # Apply styling to the DataFrame
#     def highlight_rows(row):
#         # BUG: why is it row.name and not index?
#         color = "background-color: #bae1ff" if row.name in selected_points else ""
#         return [color] * len(row)
#     # BUG: For some reason the highlighting only shows when I return like this.
#     # But it doesn't return a dataframe so I lose it...
#     display_df = display_df.style.apply(highlight_rows, axis=1)

ntotal = len(df)
nfiltered = len(filtered_df)
nselected = len(selected_df)
pfiltered = (nfiltered / ntotal) * 100
pselected = (nselected / ntotal) * 100
st.markdown(
    f"Total: **{ntotal:,}** | Filtered: **{nfiltered:,}** *({pfiltered:.3g}%)* | Selected: **{nselected:,}** *({pselected:.3g}%)*"
)

# render molecule images
# OPTIMIZE: this is will tank performance, so I should limit it OR handle it
# in Javascript on the frontend.
# With this implementation, it should probably be cached when the df is first
# built (unless it is >>10k rows)
if "molecule" in display_df.columns:
    with st.spinner("Rendering molecule images"):
        display_df["molecule_image"] = [
            Molecule.from_dynamic(m).to_svg(url_encode=True)
            for m in display_df.molecule
        ]

# build out conditional column configs
column_config = {}
if "link" in display_df.columns:
    # If there is a "link" column, this will display them as a clickable.
    column_config["link"] = st.column_config.LinkColumn(
        "Link",
        display_text="view",
    )
if "molecule_image" in display_df.columns:
    # If there is a "molecule_image" column, this will render the image.
    column_config["molecule_image"] = st.column_config.ImageColumn(
        label="Molecule",
        # height=300,  # --> feature request open
        # width="large",
        # pinned=True, # --> newest streamlit version only
    )

st.dataframe(
    data=display_df,
    hide_index=True,
    use_container_width=True,
    column_config=column_config,
)
