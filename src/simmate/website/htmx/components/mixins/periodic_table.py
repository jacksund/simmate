# -*- coding: utf-8 -*-


class PeriodicTableInput:
    def toggle_element(self, **kwargs):
        """Toggles an element on/off in the composition string via HTMX."""
        element = self.post_data.get("element")
        input_name = self.post_data.get("input_name", "composition")

        current_val = self.form_data.get(input_name) or ""
        elements = [e for e in current_val.split("-") if e]

        if element in elements:
            elements.remove(element)
        elif element:
            elements.append(element)

        new_val = "-".join(elements)
        self.update_form(input_name, new_val)
