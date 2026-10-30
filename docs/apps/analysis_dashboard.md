# Analysis Dashboard

--------------------------------------------------------------------------------

## About

The `analysis_dashboard` app is a dashboard for analyzing general datasets with dynamic and interactive plots. It is a [Streamlit](https://streamlit.io/) server that loads tables from the Simmate database (or example datasets) and builds plotly figures from them. The Simmate website embeds this dashboard at `/apps/analysis_dashboard/`.

--------------------------------------------------------------------------------

## Installation

1. Add `analysis_dashboard` to the list of installed Simmate apps with:
``` bash
simmate config add analysis_dashboard
```

2. Install Streamlit in the same environment as Simmate:
``` bash
uv pip install streamlit
```

3. Start the Streamlit server (it runs at `http://localhost:8501/` by default):
``` python
from simmate.apps.analysis_dashboard.command_line import start

start(port=8501, address=None)
```

4. (optional) If the Streamlit server runs at a different address, set the `ANALYSIS_DASHBOARD_URL` environment variable so the Simmate website can find it.

--------------------------------------------------------------------------------
