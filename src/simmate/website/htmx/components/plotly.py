# -*- coding: utf-8 -*-

from django.http import JsonResponse
from .base import HtmxComponent

class PlotlyStreamingComponent(HtmxComponent):
    """
    A base class for Plotly components that stream new data points
    without fully redrawing the component HTML.
    
    Subclasses should implement `get_new_data()` to return a dictionary 
    like `{'x': [new_x], 'y': [new_y]}`.
    """
    max_points: int = 10000

    def get_new_data(self) -> dict:
        """
        Return the newly added data points. 
        Example: {'x': [time.time()], 'y': [25.0]}
        """
        raise NotImplementedError("Subclasses must implement get_new_data()")

    def stream_data(self, **kwargs):
        """
        HTMX endpoint to retrieve the latest data and return a JSON action
        to extend the plotly trace on the client side.
        """
        new_data = self.get_new_data()
        
        # Format the action for our htmx_utils.js
        action = {
            "extendPlotlyTrace": [
                f"{self.component_id}-plotly", 
                new_data.get("x", []), 
                new_data.get("y", []),
                self.max_points
            ]
        }
        
        return JsonResponse([action], safe=False)
