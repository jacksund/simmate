# -*- coding: utf-8 -*-

from django.http import JsonResponse

from .base import HtmxComponent


class ExampleComponent(HtmxComponent):

    template_name: str = "htmx/example_form.html"

    status_options = [
        (o, o)
        for o in [
            "option one",
            "option two",
            "option three",
        ]
    ]

    def mount(self, request):
        pass

    def run_some_js(self, request) -> JsonResponse:
        js_actions = [
            {"showAlert": ["Hello from Django!"]},
            {"highlight": ["#result"]},
        ]
        return JsonResponse(js_actions, safe=False)

    def add_molecule_image(self, request):
        from simmate.toolkit import Molecule

        self.js_actions = [
            {
                "add_mol_viewer": [
                    "jacks-molecule",
                    Molecule.from_smiles("CCCCCCO").to_sdf(),
                    200,
                    300,
                ]
            }
        ]

    def update_selection_test(self, request):
        self.new_selection = True
        self.js_actions = [
            {"refresh_select2": []},
        ]
