# Creating Web Components

**Components** allow you to build interactive web pages using Python and HTML without writing JavaScript. They function like mini-views that update instantly when users interact with them.

While standard Django views are static, components use [HTMX](https://htmx.org/) to handle real-time updates—such as updating a list or a dashboard—without a full page refresh.

---

## When to Use Components
Use components only when you need real-time interactivity. Static HTML and standard Django views are preferred for simpler pages. Ideal use cases include:

*   Dynamic submission forms that change based on user input.
*   Dashboards requiring real-time data updates.
*   Interactive scientific elements like molecule sketchers or live filters.

---

## How It Works

All interactive components are centered on the `HtmxComponent` class. Each component consists of a **Python Class** (logic) and an **HTML Template** (layout).

### Registration and Rendering

1.  **Discovery**: Components are automatically found if placed in your app's `components/` directory. Simmate converts class names (e.g., `TodoComponent`) to tags (e.g., `todo-component`).
2.  **Initial Render**: Using `{% htmx_component 'todo-component' %}` initializes the class, runs the `mount()` method, and renders the HTML.
3.  **Caching**: The instance is cached with a unique `component_id`. This allows Simmate to remember the component's state across multiple interactions.

### Managing State and Input

*   **Persistent State**: Any attribute defined on your class (e.g., `self.tasks`) stays in memory as long as the user remains on the page.
*   **User Inputs (`form_data`)**: Values from tags like `{% htmx_text_input %}` are automatically synced to the `self.form_data` dictionary. Use this to read user input or reset fields after an action.
*   **Interactivity**: When a user clicks a button or interacts with an element, an AJAX request is sent. Simmate retrieves the cached object, updates `form_data`, executes the requested Python method, and re-renders the component instantly.

---


## Basic Example: A Todo List

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

### 1. The Python Logic
Define your state and methods in `my_app/components/todo.py`:

```python
from simmate.website.htmx.components import HtmxComponent

class TodoComponent(HtmxComponent):
    template_name = "my_app/todo.html"
    
    def mount(self):
        """Initializes state when the component first renders."""
        self.tasks = []

    def add_task(self):
        """Logic triggered by a button click."""
        new_task = self.form_data.get("task")
        if new_task:
            self.tasks.append(new_task)
            self.form_data["task"] = ""  # Clear the input field
```

### 2. The Component Template
Create the layout in `my_app/templates/my_app/todo.html`:

```html+django
{% extends "htmx/form_base.html" %}

{% block form %}
    <h3>My Todo List</h3>
    
    {% htmx_text_input name="task" placeholder="Enter a new task..." %}
    {% htmx_button method_name="add_task" label="Add Task" %}

    <ul>
        {% for t in component.tasks %}
            <li>{{ t }}</li>
        {% empty %}
            <li>No tasks yet!</li>
        {% endfor %}
    </ul>
{% endblock %}
```

### 3. Usage in a View
Render the component in your main template (`my_app/templates/my_app/home.html`):

```html+django
{% extends "core_components/site_base.html" %}

{% block body %}
    <div class="container">
        {% htmx_component 'todo-component' %}
    </div>
{% endblock %}
```

---

## Lifecycle Hooks

Override these methods to control component behavior:

*   `mount()`: Called once during the first initialization.
*   `pre_parse()`: Called before AJAX POST data is processed.
*   `post_parse()`: Called after POST data is applied to `self.form_data`.
*   `process()`: The default method triggered if an interactive element (like a button) does not specify a `method_name`.
