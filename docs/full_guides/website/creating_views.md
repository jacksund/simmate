# Creating Web Views

Simmate uses the [Django web framework](https://www.djangoproject.com/) for its website. This guide covers how to create standard Django views and templates while integrating them into the Simmate ecosystem.

--------------------------

## Django vs. Simmate

Simmate does not do anything special with views—we use standard Django practices. You can follow [Django's official guides](https://docs.djangoproject.com/en/5.2/topics/http/) for in-depth tutorials on views, URLs, and templates.

However, Simmate provides:

1.  **A Base Template:** `core/site_base.html` provides the standard navbar, footer, and styling (Bootstrap, HTMX, Plotly, etc.).
2.  **Automatic Registration:** Your app's `urls.py` is automatically included in the main website.
3.  **HTMX Integration:** Easily embed interactive components.

--------------------------

## Basic Example

In your app, follow Django's best practices for template organization by namespacing them within a folder named after your app. This prevents template name collisions during collection.

**Recommended Structure:**
```text
my_app/
├── templates/
│   └── my_app/
│       └── home.html
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
    return render(request, "my_app/home.html", context)
```

### 3. The Template

In `my_app/templates/my_app/home.html`, extend the Simmate base template and fill in the `tabtitle` and `body` blocks.

```html+django
{% extends "core/site_base.html" %}

{% block tabtitle %}My App Home - Simmate{% endblock %}

{% block body %}
    <h1>Hello, {{ name }}!</h1>
    <p>This is a standard Django view using the Simmate base template.</p>
{% endblock %}
```

--------------------------

## Integrating Interactive Components

To add an interactive Simmate component to your view, follow these steps:

1.  **Embed the component** using the `{% htmx_component %}` tag.

Note that `core/site_base.html` already includes the HTMX library and necessary scripts. Furthermore, Simmate automatically loads the `htmx` and several other tag libraries for you, so you do not need to use `{% load htmx %}` in your templates.

### Example Template with Component

```html+django
{% extends "core/site_base.html" %}

{% block body %}
    <h1>My App Dashboard</h1>
    
    <div class="card p-3 shadow-sm border border-secondary rounded">
        <!-- Embedding an interactive component -->
        {% htmx_component 'my-interactive-form' %}
    </div>
{% endblock %}
```

For more details on building the component itself, see the [Creating Components guide](/full_guides/website/creating_components/overview.md).

--------------------------

## How views are registered

In Simmate, you don't need to manually add your app's URLs to the main project. We automatically register your app's `urls.py` to a path matching your app's name.

For example, if your app is named `my_app`, it will be available at:

- `http://127.0.0.1:8000/apps/my_app/`

Everything in your `urls.py` will be mapped to a namespace matching your app's name. You can link to your home page using `{% url 'my_app:home' %}`.
