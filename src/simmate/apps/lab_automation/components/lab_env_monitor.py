# -*- coding: utf-8 -*-

import random
from datetime import datetime

import plotly.graph_objects as go

from simmate.website.htmx.components.base import HtmxComponent


class AmbientTempComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(22.4)
        else:
            cls.history_x.append(t)
            target = 22.4
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.1) + random.gauss(0, 0.2)
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_val = y[-1]

        fig = go.Figure()

        # Add Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_val,
                number={"suffix": "°C"},
                title={"text": "Ambient Temp", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [10, 40],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "#28a745"},
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
                line=dict(color="#28a745", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Temp (°C)", anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=250,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}


class HumidityComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(35.0)
        else:
            cls.history_x.append(t)
            target = 35.0
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.1) + random.gauss(0, 0.5)
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_val = y[-1]

        fig = go.Figure()

        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_val,
                number={"suffix": "%"},
                title={"text": "Humidity", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [0, 100],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "#17a2b8"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="#17a2b8", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="Humidity (%)", anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=250,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}


class AirQualityComponent(HtmxComponent):
    template_name: str = "lab_automation/components/streaming_plot.html"

    history_x = []
    history_y = []
    max_points = 1000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(42.0)
        else:
            cls.history_x.append(t)
            target = 42.0
            current = cls.history_y[-1]
            diff = target - current
            new_y = current + (diff * 0.1) + random.gauss(0, 1.0)
            cls.history_y.append(new_y)

            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points :]
                cls.history_y = cls.history_y[-cls.max_points :]

        return cls.history_x, cls.history_y

    @property
    def figure(self):
        x, y = self.get_latest_data()
        x_datetime = [datetime.fromtimestamp(val) for val in x]
        current_val = y[-1]

        fig = go.Figure()

        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_val,
                number={"suffix": " ppb"},
                title={"text": "Air Quality", "font": {"size": 14}},
                gauge={
                    "axis": {
                        "range": [0, 500],
                        "tickwidth": 1,
                        "tickcolor": "darkblue",
                    },
                    "bar": {"color": "#007bff"},
                    "bgcolor": "white",
                    "borderwidth": 2,
                    "bordercolor": "gray",
                },
                domain={"x": [0.1, 0.9], "y": [0.55, 1]},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=x_datetime,
                y=y,
                mode="lines",
                line=dict(color="#007bff", width=2),
            )
        )

        fig.update_layout(
            xaxis=dict(domain=[0, 1]),
            yaxis=dict(domain=[0, 0.45], title="VOC (ppb)", anchor="x"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=250,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        return {"x": [last_x_dt], "y": [y[-1]]}
