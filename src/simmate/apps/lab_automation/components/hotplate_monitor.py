# -*- coding: utf-8 -*-

import random
from datetime import datetime

import plotly.graph_objects as go

from simmate.website.htmx.components.base import HtmxComponent


class HotplateTempComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(25.0)  # Room temp start
        else:
            cls.history_x.append(t)
            # Drift towards 150C
            target = 150.0
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.05) + random.gauss(0, 0.5)
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_temp = y[-1]

        fig = go.Figure()

        # Add Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_temp,
                number={"suffix": "°C"},
                title={"text": "Temperature", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [None, 300],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "darkred"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        # Add Line Plot
        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="darkred", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Temp (°C)", anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=350,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}


class HotplateStirComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(0.0)
        else:
            cls.history_x.append(t)
            target = 60.0  # 60%
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.1) + random.gauss(0, 1.0)
            new_y = max(0, min(100, new_y))
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_stir = y[-1]

        fig = go.Figure()

        # Add Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_stir,
                number={"suffix": "%"},
                title={"text": "Stir Speed", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [None, 100],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "darkblue"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        # Add Line Plot
        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="darkblue", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Speed (%)", range=[0, 100], anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=350,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}


class Hotplate2TempComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(25.0)  # Room temp start
        else:
            cls.history_x.append(t)
            # Drift towards 80C
            target = 80.0
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.03) + random.gauss(0, 0.3)
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_temp = y[-1]

        fig = go.Figure()

        # Add Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_temp,
                number={"suffix": "°C"},
                title={"text": "Temperature", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [None, 300],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "orange"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        # Add Line Plot
        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="orange", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Temp (°C)", anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=350,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}


class Hotplate2StirComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(0.0)
        else:
            cls.history_x.append(t)
            target = 30.0  # 30%
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.1) + random.gauss(0, 0.5)
            new_y = max(0, min(100, new_y))
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_stir = y[-1]

        fig = go.Figure()

        # Add Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_stir,
                number={"suffix": "%"},
                title={"text": "Stir Speed", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [None, 100],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "cyan"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        # Add Line Plot
        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="cyan", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Speed (%)", range=[0, 100], anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=350,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}
