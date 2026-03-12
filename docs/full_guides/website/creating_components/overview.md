
## What are web components?

**Components let you build interactive web pages using Python and HTML**, without needing JavaScript (we handle that part for you). So components work like mini Django views that automatically update when users interact with them.

We need components because standard Django views are static HTML by default. Once your view+template is loaded, it does not change until you navigate to a new link or refresh your page. Components come into play when you want real-time interactivity—such as clicking a button and having a section of the page update, or checking a box and having extra form options appear instantly—all without a full page refresh.

Simmate's web components integrate [HTMX](https://htmx.org/) and AJAX calls, allowing you to build these interactive features entirely in Python.

--------------------------

## Do I need components?

Avoid overcomplicating things if you can. You can achieve quite a bit just with static HTML that ships with standard Django views. You only need components when you have:

- A dynamic submission form (e.g., one that changes as a user fills it out).
- A need for real-time data updates (e.g., a dashboard that updates without refreshing).
- Complex interactive elements like molecule sketchers or live search filters.

Before diving into components, ensure you are comfortable with HTML and [Django Templates](https://docs.djangoproject.com/en/5.2/topics/templates/).

!!! tip
    A beginner-friendly alternative for building dynamic dashboards is [Streamlit](https://streamlit.io/). You can embed a Streamlit app within a Simmate page using an `iframe`:
    ``` html+django
    <iframe src="{{ dashboard_url }}?embed=true"
            style="height:150vh;
                   width:100%;
                   border:none">
    </iframe>
    ```

--------------------------

## Core Concepts

Simmate's HTMX framework is built around the `HtmxComponent` class. Each component consists of:

1.  **A Python Class**: Inherits from `HtmxComponent` and defines the backend logic.
2.  **An HTML Template**: Defines the frontend layout and uses custom `htmx_` tags.

Components are automatically discovered if they are located in a `components/` submodule of your app.

--------------------------

## Basic Example

In your app, set up the following structure:
```text
my_app/
├── components/
│   ├── __init__.py
│   └── todo.py
├── templates/
│   ├── my_app/
│   │   └── todo.html
│   └── my_homepage.html
├── urls.py
└── views.py
```

### 1. The Component (Python)

In `my_app/components/todo.py`:

```python
from simmate.website.htmx.components import HtmxComponent

class TodoComponent(HtmxComponent):
    template_name = "my_app/todo.html"
    
    task = ""
    tasks = []

    def add_task(self):
        if self.task:
            self.tasks.append(self.task)
            self.task = ""  # Reset the input
```

### 2. The Component Template (HTML)

In `my_app/templates/my_app/todo.html`:

```html+django
{% load htmx %}

<div id="{{ component.component_id }}">
    <h3>My Todo List</h3>
    
    {% htmx_text_input name="task" placeholder="Enter a new task..." %}
    {% htmx_button method_name="add_task" label="Add Task" %}

    <ul class="mt-3">
        {% for t in tasks %}
            <li>{{ t }}</li>
        {% empty %}
            <li>No tasks yet!</li>
        {% endfor %}
    </ul>
</div>
```

### 3. Using the Component in a View

In your main template (`my_app/templates/my_homepage.html`):

```html+django
{% load htmx %}
<!DOCTYPE html>
<html>
    <head>
        <title>Home</title>
        {% htmx_cdn_script %}
    </head>
    <body>
        <h1>Welcome to my App</h1>
        <div class="container">
            {% htmx_component 'todo-component' %}
        </div>
    </body>
</html>
```

--------------------------

## How it works

1.  **Registration**: Simmate scans your app's `components/` folder and registers `TodoComponent` under the name `todo-component`.
2.  **Initial Render**: When `{% htmx_component 'todo-component' %}` is called, Simmate initializes the class, calls its `mount()` method, and renders the template.
3.  **Caching**: The initialized object is stored in a local cache with a unique `component_id`.
4.  **Interactivity**: When you click the "Add Task" button, HTMX sends an AJAX request to Simmate. Simmate retrieves the object from cache, updates its `task` attribute with the input value, calls `add_task()`, and re-renders the component.
