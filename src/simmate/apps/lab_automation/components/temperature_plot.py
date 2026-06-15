# -*- coding: utf-8 -*-

import math
import random
from datetime import datetime

import plotly.graph_objects as go

from simmate.website.htmx.components.base import HtmxComponent
from simmate.website.htmx.components.plotly import PlotlyStreamingComponent


class TemperaturePlotComponent(HtmxComponent):

    template_name: str = "lab_automation/components/temperature_plot.html"
    
    history_x = []
    history_y = []
    max_points = 10000

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(50.0)
        else:
            # Generate 1 new point based on the last one
            cls.history_x.append(t)
            new_y = cls.history_y[-1] + random.gauss(0, 0.5)
            cls.history_y.append(new_y)
            
            # Cap at max_points
            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points:]
                cls.history_y = cls.history_y[-cls.max_points:]
                
        return cls.history_x, cls.history_y

    @property
    def plot_html(self):
        x, y = self.get_latest_data()
        
        # Format the x-axis to be datetime
        x_datetime = [datetime.fromtimestamp(val) for val in x]

        fig = go.Figure(data=go.Scatter(x=x_datetime, y=y, mode='lines+markers'))
        fig.update_layout(
            title="Temperature over Time",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            margin=dict(l=40, r=20, t=40, b=40),
            height=300,
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)


class StreamingTemperaturePlotComponent(PlotlyStreamingComponent):

    template_name: str = "lab_automation/components/streaming_temperature_plot.html"
    
    history_x = []
    history_y = []

    @classmethod
    def get_latest_data(cls):
        t = datetime.now().timestamp()
        if not cls.history_x:
            cls.history_x.append(t)
            cls.history_y.append(50.0)
        else:
            # Generate 1 new point based on the last one
            cls.history_x.append(t)
            new_y = cls.history_y[-1] + random.gauss(0, 0.5)
            cls.history_y.append(new_y)
            
            # Cap at max_points (inherited from PlotlyStreamingComponent, default 10000)
            if len(cls.history_x) > cls.max_points:
                cls.history_x = cls.history_x[-cls.max_points:]
                cls.history_y = cls.history_y[-cls.max_points:]
                
        return cls.history_x, cls.history_y

    @property
    def plot_html(self):
        x, y = self.get_latest_data()
        
        # Format the x-axis to be datetime
        x_datetime = [datetime.fromtimestamp(val) for val in x]

        fig = go.Figure(data=go.Scatter(x=x_datetime, y=y, mode='lines+markers'))
        fig.update_layout(
            title="Streaming Temperature over Time",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            margin=dict(l=40, r=20, t=40, b=40),
            height=300,
        )
        return fig.to_html(full_html=False, include_plotlyjs=False, div_id=f"{self.component_id}-plotly")

    def get_new_data(self) -> dict:
        x, y = self.get_latest_data()
        last_x_dt = datetime.fromtimestamp(x[-1]).strftime('%Y-%m-%d %H:%M:%S.%f')
        return {
            'x': [last_x_dt],
            'y': [y[-1]]
        }
