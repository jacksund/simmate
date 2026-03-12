
## Django vs. Simmate

Simmate does not do anything special with views—we just use the [Django web framework](https://www.djangoproject.com/). You can follow [Django's official guides](https://docs.djangoproject.com/en/5.2/topics/http/) to create web views, URLs, and templates.

However, Simmate provides a powerful system for embedding **interactive web components** within these standard views using HTMX.

--------------------------

## Basic Example

In your app, set up the following:
```text
my_app/
├── templates/
│   └── my_homepage.html
├── urls.py
└── views.py
```

### 1. The URL Mapping

In `my_app/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
```

### 2. The View Logic

In `my_app/views.py`:

```python
from django.shortcuts import render

def home(request):
    context = {"name": "Jane Doe"}
    return render(request, "my_homepage.html", context)
```

### 3. The Template

In `my_app/templates/my_homepage.html`:

```html+django
<!DOCTYPE html>
<html>
    <head>
        <title>Home Page</title>
    </head>
    <body>
        <h1>Hello, {{ name }}!</h1>
        <p>This is a standard Django view.</p>
    </body>
</html>
```

--------------------------

## Integrating Interactive Components

To add a Simmate component to your view, follow these steps:

1.  **Load the `htmx` tag library** in your template.
2.  **Add the HTMX script** in the `<head>` (via `{% htmx_cdn_script %}`).
3.  **Embed the component** using the `{% htmx_component %}` tag.

### Example Template with Component

```html+django
{% load htmx %}
<!DOCTYPE html>
<html>
    <head>
        <title>Home Page</title>
        {% htmx_cdn_script %}
    </head>
    <body>
        <h1>Hello, {{ name }}!</h1>
        
        <!-- Embedding an interactive component -->
        <div class="card p-3 shadow-sm border border-secondary rounded">
            {% htmx_component 'my-interactive-form' %}
        </div>
    </body>
</html>
```

For more details on building the component itself, see the [Creating Components guide](/full_guides/website/creating_components/overview.md).

--------------------------

## How views are registered

In Simmate, you don't need to manually add your app's URLs to the main project. We automatically register your app's `urls.py` to a path matching your app's name.

For example, if your app is named `my_app`, it will be available at:

- `http://127.0.0.1:8000/apps/my_app/`

Everything in your `urls.py` will be mapped to a namespace matching your app's name.
