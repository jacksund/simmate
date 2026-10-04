# -*- coding: utf-8 -*-

import random
from datetime import datetime

import plotly.graph_objects as go

from simmate.website.htmx.components.base import HtmxComponent
from simmate.website.htmx.components.utils import style_dashboard_figure


class SimulatedSensorComponent(HtmxComponent):
    """
    A card showing the live reading of a (simulated) sensor along with a
    small history chart. Readings drift from `start` towards `target` with
    some gaussian noise.

    Each subclass automatically gets its own `history_x` and `history_y` lists
    so that every sensor keeps a separate history.
    """

    template_name: str = "lab_automation/components/sensor_card.html"

    refresh_interval: str = "2s"

    label: str = None
    units: str = None
    icon: str = "bi-activity"
    color: str = "#0d6efd"
    decimals: int = 1

    start: float = None
    target: float = None
    rate: float = 0.1
    """
    Fraction of the remaining distance to `target` covered on each reading.
    """
    noise: float = 0.5
    value_range: tuple[float, float] = None
    """
    Readings are clipped to this range. Also used as the chart's y-axis range.
    """
    nominal_range: tuple[float, float] = None
    """
    Readings outside of this range are labeled as "out of range".
    """

    history_x: list[datetime] = None
    history_y: list[float] = None
    max_points: int = 1000

    borderless: bool = False
    """
    Drops the card's border and shadow, e.g. when it sits inside another card.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.history_x = []
        cls.history_y = []

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        x, y = self.get_latest_data()
        current_value = y[-1]

        status_text, status_theme = self.get_status(current_value)
        ctx.update(
            current_value=f"{current_value:.{self.decimals}f}",
            status_text=status_text,
            status_theme=status_theme,
            figure=self.get_figure(x, y),
        )
        return ctx

    def get_status(self, value: float) -> tuple[str, str]:
        """
        Labels a reading as nominal, ramping (still on its way from `start` to
        `target`), or out of range. Returns the label and its bootstrap color.
        """
        if not self.nominal_range:
            return "nominal", "success"
        low, high = self.nominal_range
        if low <= value <= high:
            return "nominal", "success"
        if min(self.start, self.target) <= value <= max(self.start, self.target):
            return "ramping", "info"
        return "out of range", "warning"

    def get_figure(self, x: list[datetime], y: list[float]) -> go.Figure:
        figure = go.Figure(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color=self.color, width=2),
                fill="tozeroy" if self.value_range else None,
                fillcolor=self._to_rgba(self.color, 0.08),
                hovertemplate=f"%{{y:.{self.decimals}f}} {self.units}<extra></extra>",
            )
        )
        figure.add_hline(
            y=self.target,
            line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dot"),
        )
        style_dashboard_figure(figure)
        figure.update_layout(
            height=160,
            margin=dict(t=5, r=5, l=40, b=25),
            font=dict(size=11),
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(range=self.value_range),
        )
        return figure

    @staticmethod
    def _to_rgba(hex_color: str, alpha: float) -> str:
        r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
        return f"rgba({r},{g},{b},{alpha})"

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    @classmethod
    def get_latest_data(cls) -> tuple[list[datetime], list[float]]:
        """
        Simulates a new sensor reading and returns the full history.
        """
        cls.history_x.append(datetime.now())
        if not cls.history_y:
            cls.history_y.append(cls.start)
        else:
            current = cls.history_y[-1]
            new_y = (
                current + (cls.target - current) * cls.rate + random.gauss(0, cls.noise)
            )
            if cls.value_range:
                new_y = max(cls.value_range[0], min(cls.value_range[1], new_y))
            cls.history_y.append(new_y)

        if len(cls.history_x) > cls.max_points:
            del cls.history_x[: -cls.max_points]
            del cls.history_y[: -cls.max_points]

        return cls.history_x, cls.history_y


# -----------------------------------------------------------------------------
# Lab environment
# -----------------------------------------------------------------------------


class AmbientTempComponent(SimulatedSensorComponent):
    label = "Ambient Temp"
    units = "°C"
    icon = "bi-thermometer-half"
    color = "#009485"
    start = 22.4
    target = 22.4
    noise = 0.2
    nominal_range = (18, 26)


class HumidityComponent(SimulatedSensorComponent):
    label = "Humidity"
    units = "%"
    icon = "bi-droplet"
    color = "#0dcaf0"
    start = 35.0
    target = 35.0
    noise = 0.5
    value_range = (0, 100)
    nominal_range = (30, 50)


class AirQualityComponent(SimulatedSensorComponent):
    label = "Air Quality (VOC)"
    units = "ppb"
    icon = "bi-wind"
    color = "#0d6efd"
    decimals = 0
    start = 42.0
    target = 42.0
    noise = 1.0
    nominal_range = (0, 220)


# -----------------------------------------------------------------------------
# Hotplates
# -----------------------------------------------------------------------------


class HotplateTempSensor(SimulatedSensorComponent):
    borderless = True
    label = "Temperature"
    units = "°C"
    icon = "bi-thermometer-high"


class HotplateStirSensor(SimulatedSensorComponent):
    borderless = True
    label = "Stir Speed"
    units = "%"
    icon = "bi-arrow-repeat"
    color = "#6f42c1"
    decimals = 0
    start = 0.0
    value_range = (0, 100)


class HotplateTempComponent(HotplateTempSensor):
    color = "#dc3545"
    start = 25.0
    target = 150.0
    rate = 0.05
    noise = 0.5
    nominal_range = (140, 160)


class HotplateStirComponent(HotplateStirSensor):
    target = 60.0
    noise = 1.0
    nominal_range = (50, 70)


class Hotplate2TempComponent(HotplateTempSensor):
    color = "#fd7e14"
    start = 25.0
    target = 80.0
    rate = 0.03
    noise = 0.3
    nominal_range = (75, 85)


class Hotplate2StirComponent(HotplateStirSensor):
    target = 30.0
    noise = 0.5
    nominal_range = (25, 35)
