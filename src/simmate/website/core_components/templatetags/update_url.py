# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def update_url(context, **kwargs):
    """
    Returns the current URL with updated GET parameters.

    Example use:
    ``` html
    {% load update_url %}
    <a href="{% update_url page=2 sort='name' %}">Next Page</a>
    ```

    DEV NOTE: if we want this to be done on the frontend, we could use...

    ``` html
    <a id="set-format-json" href="#">Set format=json</a>
    <script>
        function buildUpdatedUrl(param, value) {
          let url = new URL(window.location.href);
          if (value === null ) {
            url.searchParams.delete(param);
          } else {
            url.searchParams.set(param, value);
          }
          return url.pathname + url.search;
        }

        document.getElementById('set-format-json').href = buildUpdatedUrl('format', 'json');
    </script>
    ```

    """
    request = context["request"]
    get_params = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == "":
            get_params.pop(k, None)
        else:
            get_params[k] = v
    query = get_params.urlencode()
    return f"?{query}"
