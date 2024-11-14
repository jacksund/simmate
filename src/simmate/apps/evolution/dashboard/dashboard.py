# -*- coding: utf-8 -*-

# To Do:
# 1. Pull the active searches
# 2. set up streamlit
# 3. use already existing plotly methods

import time

import nglview
import streamlit

from simmate.apps.evolution.models import FixedCompositionSearch
from simmate.database import connect

streamlit.set_page_config(page_title="Active Searches", layout="wide")
# get active fixed composition searches
active_searches = FixedCompositionSearch.objects.filter(finished_at__isnull=True)
if len(active_searches) == 0:
    streamlit.write("No Active Searches")
    time.sleep(10)
    streamlit.rerun()

# create tabs for each search
tab_names = []
for search in active_searches:
    tab_names.append(str(search.id))
tabs = streamlit.tabs(tab_names)

# iterate over each tab and plot
for tab, search in zip(tabs, active_searches):
    with tab:
        try:
            streamlit.header(f"{search.composition}")
            col1, col2 = streamlit.columns(2)
            # Create each desired plot
            with col1:
                streamlit.plotly_chart(search.get_fitness_convergence_plot().to_dict())
                # streamlit.plotly_chart(search.get_fitness_distribution_plot().to_dict())
                streamlit.plotly_chart(search.get_subworkflow_times_plot().to_dict())
                streamlit.plotly_chart(search.get_source_proportions_plot().to_dict())
            with col2:
                streamlit.plotly_chart(
                    search.get_staged_series_convergence_plot().to_dict()
                )
                streamlit.plotly_chart(
                    search.get_staged_series_histogram_plot().to_dict()
                )
                streamlit.plotly_chart(search.get_staged_series_times_plot().to_dict())
        except:
            streamlit.write("Search has not progressed far enough. Waiting.")
time.sleep(10)
streamlit.rerun()
