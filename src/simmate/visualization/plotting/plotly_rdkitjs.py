# -*- coding: utf-8 -*-

import uuid
import webbrowser
from pathlib import Path

from django.template import Template

from simmate.visualization.plotting.plotly import PlotlyFigure


class PlotlyRdkitjsFigure(PlotlyFigure):

    @classmethod
    def view_plot(cls, parent_class, **kwargs):

        # This is a different than the normal Plotly approach where we would
        # do something like:
        #     figure = cls.get_plot(parent_class, **kwargs)
        #     cls.apply_theme(figure)
        #     figure.show(renderer="browser")
        #
        # Instead, we need to write a custom html and then open it ourselves
        filename = cls.write_plot(parent_class, **kwargs)

        # tell default browser to open the local file
        url = f"file://{filename.absolute()}"
        webbrowser.open(url)

    @classmethod
    def write_plot(cls, parent_class, directory: Path = None, **kwargs):

        if not directory:
            directory = Path.cwd()

        # This is a different than the normal Plotly approach where we would
        # do something like:
        #     figure = cls.get_plot(parent_class, **kwargs)
        #     cls.apply_theme(figure)
        #     figure.write_html(
        #         directory / f"{cls.name}.html",
        #         include_plotlyjs="cdn",
        #     )
        #
        # Instead, we need to render the full html using our own templates
        # to ensure that
        #   1. the Rdkit.js CDN is included
        #   2. the <canvas> object is present to draw the molecule
        html_div = cls.get_html_div(parent_class, **kwargs)
        template = Template(HTML_TEMPLATE)
        full_html = template.render(
            context={"plot_div": html_div},
        )

        filename = directory / f"{cls.name}.html"
        with filename.open("w") as file:
            file.write(full_html)

        return filename

    @classmethod
    def get_html_div(cls, parent_class, div_id: str = None, **kwargs):

        # Generate a random UUID (UUID4). This is needed later to make sure
        # it uses the correct <canvas> to draw molecules.
        div_id = str(uuid.uuid4()) if not div_id else div_id

        # TODO: maybe add mol-canvas to end via a replace() call rather than in
        # the write_plot method. Passing the div_id around between methods is
        # confusing and messy

        # Make the figure and convert it to an html div
        figure = cls.get_plot(parent_class, **kwargs)
        cls.apply_theme(figure)
        html_div = figure.to_html(
            div_id=div_id,
            full_html=False,
            include_plotlyjs=False,
            post_script=RDKITJS_POST_SCRIPT,
        )

        # extra <canvas> object needed (with expected ID) to draw molecules
        html_div += CANVAS_TEMPLATE.format(div_id=div_id)
        # TODO: maybe make this optional or allow it to be elsewhere

        return html_div


# !!! Consider merging functionality with PlotlyFigure class
# TODO: move template + javascript into separate files

# For standalone export/viewing, minimal template that includes plotly+rdkit libs
# and a canvas to draw molecules on
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://unpkg.com/@rdkit/rdkit/dist/RDKit_minimal.js"></script>
    </head>
    <body>
        {{ plot_div|safe }}
    </body>
</html>
"""

CANVAS_TEMPLATE = """
<div id="mol-canvas-{div_id}" style="margin-top: 20px; z-index: 1000;"></div>
"""


# JavaScript snippet to handle hover events
# !!! Assumes you have the smiles data column given to the `customdata` kwarg:
RDKITJS_POST_SCRIPT = """
window.initRDKitModule().then(function(RDKit) {
    console.log("RDKit version: " + RDKit.version());
    window.RDKit = RDKit;

    var plot = document.getElementById('{plot_id}');
    plot.on('plotly_hover', function(data) {
        var point = data.points[0];
        var smiles = point.customdata;

        var mol = RDKit.get_mol(smiles);
        var svg = mol.get_svg();
        document.getElementById('mol-canvas-{plot_id}').innerHTML = svg;
    });

    plot.on('plotly_unhover', function(data) {
        document.getElementById('mol-canvas-{plot_id}').innerHTML = '';
    });
}).catch(() => {
    console.error("Failed to load RDKit.js");
});
"""
