# Creating Web Components

## What are web components?

**Components let you build interactive web pages using Python and HTML**, without needing JavaScript (we handle that part for you). Components work like mini Django views that automatically update when users interact with them.

Standard Django views are static HTML by default. Once your view is loaded, it does not change until you navigate to a new link or refresh the page. Components come into play when you want real-time interactivity—such as clicking a button and having a section of the page update instantly—all without a full page refresh.

Simmate's web components integrate [HTMX](https://htmx.org/) and AJAX calls, allowing you to build these interactive features entirely in Python.

--------------------------

## Do I need components?

Avoid overcomplicating things if you can. You can achieve quite a bit just with static HTML that ships with standard Django views. You only need components when you have:

- A dynamic submission form (e.g., one that changes as a user fills it out).
- A need for real-time data updates (e.g., a dashboard that updates without refreshing).
- Complex interactive elements like molecule sketchers or live search filters.

Before diving into components, ensure you are comfortable with HTML and [Django Templates](https://docs.djangoproject.com/en/5.2/topics/templates/).

!!! tip
    A beginner-friendly alternative for building dynamic dashboards is [Streamlit](https://streamlit.io/). You can embed a Streamlit app within a Simmate page using an `iframe`.

--------------------------

## Core Concepts

Simmate's HTMX framework is built around the `HtmxComponent` class. Each component consists of:

1.  **A Python Class**: Inherits from `HtmxComponent` and defines the backend logic.
2.  **An HTML Template**: Defines the frontend layout and uses custom `htmx_` tags.

Components are automatically discovered if they are located in a `components/` submodule of your app.

--------------------------

## Basic Example

In your app, set up the following structure. Note that templates are namespaced within a folder named after your app:

```text
my_app/
├── components/
│   ├── __init__.py
│   └── todo.py
├── templates/
│   └── my_app/
│       ├── todo.html
│       └── home.html
├── urls.py
└── views.py
```

### 1. The Component (Python)

In `my_app/components/todo.py`:

```python
from simmate.website.htmx.components import HtmxComponent

class TodoComponent(HtmxComponent):
    template_name = "my_app/todo.html"
    
    # Initialize instance-specific state. This method is called 
    # only once when the component is first rendered on the page.
    def mount(self):
        self.tasks = []

    def add_task(self):
        # 'task' comes from the {% htmx_text_input name="task" ... %} in our template.
        # We grab it from self.form_data, which tracks all current user inputs.
        new_task = self.form_data.get("task")
        
        if new_task:
            self.tasks.append(new_task)
            self.form_data["task"] = ""  # Reset the input field for the next task
```

### 2. The Component Template (HTML)

In `my_app/templates/my_app/todo.html`:

```html+django
<div id="{{ component.component_id }}">
    <h3>My Todo List</h3>
    
    {# 'name' must match the key we use in self.form_data #}
    {% htmx_text_input name="task" placeholder="Enter a new task..." %}
    
    {# 'method_name' must match a method in your Python class #}
    {% htmx_button method_name="add_task" label="Add Task" %}

    <ul class="mt-3">
        {# 'tasks' is an attribute on our class, so we access it via 'component' #}
        {% for t in component.tasks %}
            <li>{{ t }}</li>
        {% empty %}
            <li>No tasks yet!</li>
        {% endfor %}
    </ul>
</div>
```

### 3. Using the Component in a View

In your main template (`my_app/templates/my_app/home.html`), extend the Simmate base template and use the `{% htmx_component %}` tag.

```html+django
{% extends "core_components/site_base.html" %}

{% block body %}
    <h1>Welcome to my App</h1>
    <div class="container">
        {% htmx_component 'todo-component' %}
    </div>
{% endblock %}
```

!!! note
    Simmate automatically loads the `htmx` and several other tag libraries for you, so you do not need to use `{% load htmx %}`.

--------------------------

## Attributes and State

### Persistent State
Any attribute you define on your instance (like `self.tasks` in our example) will persist in memory across multiple AJAX calls as long as the user stays on the same page. This is because Simmate caches your component instances between requests.

### User Inputs (`form_data`)
When using Simmate's input tags (like `{% htmx_text_input %}`), the values are automatically collected and sent to the backend. These values are available in the `self.form_data` dictionary. 

Use `form_data` for:
- Grabbing current inputs from the user.
- Resetting input fields after an action.
- Passing finalized data to model creation (e.g., when saving to a database).

--------------------------

## Lifecycle Hooks

You can override these methods in your `HtmxComponent` to hook into its lifecycle:

-   `mount()`: Called when the component is first initialized. Use this for setting up initial state.
-   `pre_parse()`: Called before POST data is parsed from an AJAX request.
-   `post_parse()`: Called after POST data is parsed and applied to `self.form_data`.
-   `process()`: The default method called during an AJAX request if no specific `method_name` is provided to a button.

--------------------------

## How it works

1.  **Registration**: Simmate scans your app's `components/` folder and registers classes that inherit from `HtmxComponent`. The name is automatically converted (e.g., `TodoComponent` becomes `todo-component`).
2.  **Initial Render**: When `{% htmx_component 'todo-component' %}` is encountered, Simmate initializes the class, calls `mount()`, and renders the template.
3.  **Caching**: The initialized object is stored in a local cache with a unique `component_id`.
4.  **Interactivity**: When a user interacts with an element (e.g., clicking a button), HTMX sends an AJAX request. Simmate retrieves the object from cache, updates `self.form_data` with the new values, calls the requested method, and re-renders the component.
