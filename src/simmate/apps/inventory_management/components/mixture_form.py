# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Mixture


class MixtureForm(DynamicTableForm):
    table = Mixture

    html_display_name = "Mixtures"
    html_description_short = (
        "Mixtures are the combination of two or more substances. "
        "For example, a solution would be a mixture of two substances: NaCl and water. "
        "This table includes mixtures of both specified and unspecified ratios, "
        "meaning 'salt water' and '0.1M salt water' can be separate entries."
    )
