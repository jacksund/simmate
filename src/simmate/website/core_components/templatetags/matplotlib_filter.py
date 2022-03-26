# -*- coding: utf-8 -*-

from io import BytesIO
import base64

from django import template
from django.utils.safestring import mark_safe

# We need a registration instance in order to configure everything with Django
register = template.Library()


@register.filter(name="matplotlib_figure", is_safe=True)
def matplotlib_to_html(plot):
    """
    Converts a matplotlib figure into an html element.
    """

    # Lmao I have no idea how this works and I just got lucky when following
    # these stack overflow posts... I should switch to plotly ASAP so I can
    # remove this filter.
    #   https://stackoverflow.com/questions/14824522/
    #   https://stackoverflow.com/questions/40534715/
    # Alternatively, I could rewrite this function to save a randomly generated
    # file to the /static/runtime folder and then passing back an html <img> tag
    # that points back to this image.

    figdata = BytesIO()
    plot.savefig(figdata, format="png")
    figdata.seek(0)
    data = figdata.getvalue()
    data_decoded = base64.b64encode(data).decode("utf-8").replace("\n", "")
    html = f"""
    <img id="ItemPreview" class="img-fluid" src="data:image/png;base64,{data_decoded}">
    """

    # BUG: every time this filter is called, I recieve the following warning:
    #
    # .../lib/python3.10/site-packages/pymatgen/util/plotting.py:48: UserWarning:
    # Starting a Matplotlib GUI outside of the main thread will likely fail.
    # plt.figure(figsize=(width, height), facecolor="w", dpi=dpi)
    #
    # This doesn't seem to cause any issues, so I ignore it for now.

    # Because we added new html to our script, we need to have Django check it
    # ensure it safe before returning. Read more about this here:
    # https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#filters-and-auto-escaping
    return mark_safe(html)
