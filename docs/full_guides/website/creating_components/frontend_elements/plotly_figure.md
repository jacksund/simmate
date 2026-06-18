Displays a Plotly figure as an interactive HTML element.

We use [Plotly](https://plotly.com/python/) under the hood to generate graphs. This component safely converts a python `Figure` to HTML, and optionally supports dynamic updates via HTMX.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_plotly_figure component.figure %}
    ```

=== "backend (python)"

    ``` python
    import plotly.graph_objects as go
    from simmate.website.htmx.components.base import HtmxComponent

    class ExamplePlotComponent(HtmxComponent):

        @property
        def figure(self):
            # Generate the figure to display
            fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[10, 15, 13]))
            return fig
    ```

## Parameters

| Parameter | Description |
| --------- | ----------- |
| `figure` | The `plotly.graph_objects.Figure` object to render.<br><small>*Type: `Figure`, Default: —*</small> |
| `div_id` | The ID for the wrapping HTML div. Useful if you have multiple plots. If left as `None` while streaming, an ID will be generated automatically based on the component's ID.<br><small>*Type: `str`, Default: `None`*</small> |
| `stream_interval` | Interval (in seconds) to query the backend for new data and extend the traces. If `None`, no polling occurs.<br><small>*Type: `int`, Default: `None`*</small> |
| `stream_method` | The name of the backend method that returns the new data dictionary (e.g., `{"x": [...], "y": [...]}`). Only used if `stream_interval` is set.<br><small>*Type: `str`, Default: `"get_new_data"`*</small> |
| `max_points` | The maximum number of points to keep when streaming data to prevent memory overflow in the browser.<br><small>*Type: `int`, Default: `10000`*</small> |

## Dynamic Updates

If you have data that changes over time (like monitoring lab equipment), HTMX allows for dynamic updates to your graph. There are two primary ways to do this:

### 1. Full Redraw (Easy way)

This approach completely replaces the figure element on a set interval using HTMX polling (`htmx_refresh`). It is simple to implement but less efficient for large datasets or frequent updates.

=== "frontend (html+django)"

    ``` html+django
    {% extends "htmx/form_base.html" %}

    {% block form %}
        <form class="m-0 p-0">
            {% htmx_refresh refresh_loop="1s" indicator="None" %}
            {% htmx_plotly_figure component.figure %}
        </form>
    {% endblock %}
    ```

=== "backend (python)"

    ``` python
    import plotly.graph_objects as go
    from simmate.website.htmx.components.base import HtmxComponent

    class TemperaturePlotComponent(HtmxComponent):

        template_name: str = "my_app/components/temperature_plot.html"

        @property
        def figure(self):
            # Generate the latest figure. This is called on every refresh.
            fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[10, 15, 13]))
            return fig
    ```

### 2. Streaming Update (Efficient way)

This approach uses Plotly's `extendTraces` functionality to append new data to the chart via JavaScript. This is much faster for large line/scatter plots and ideal for live dashboards. Both of these approaches can be seen in the lab automation app homepage.

=== "frontend (html+django)"

    ``` html+django
    {% extends "htmx/form_base.html" %}

    {% block form %}
        <form class="m-0 p-0">
            <!-- 
            We pass `stream_interval` which tells HTMX to poll for new data
            using `stream_method` (default: get_new_data).
            -->
            {% htmx_plotly_figure component.figure stream_interval=1 %}
        </form>
    {% endblock %}
    ```

=== "backend (python)"

    ``` python
    import plotly.graph_objects as go
    from simmate.website.htmx.components.base import HtmxComponent

    class StreamingTemperaturePlotComponent(HtmxComponent):

        template_name: str = "my_app/components/streaming_plot.html"

        @property
        def figure(self):
            # Generate the initial base figure. This is only called once.
            fig = go.Figure(data=go.Scatter(x=[1, 2], y=[10, 15]))
            return fig

        def get_new_data(self) -> dict:
            # Returns a dictionary of lists corresponding to new x/y data to append.
            # This method is polled every `stream_interval` seconds.
            return {
                "x": [3], 
                "y": [13]
            }
    ```
