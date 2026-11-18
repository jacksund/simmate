
## Component Lifecycle

Each `HtmxComponent` has several hooks you can override to control its behavior:

-   `mount()`: Called when the component is first initialized (e.g., when the page is first loaded). Use this for setting initial state.
-   `pre_parse()`: Called before POST data is parsed from an AJAX request.
-   `post_parse()`: Called after POST data is parsed and applied to the component's attributes.
-   `process()`: The default method called during an AJAX request if no specific `method_name` is provided.

--------------------------

## Form Handling with `TableComponent`

For components that interact with the database, Simmate provides the `TableComponent` class. This handles common CRUD operations (Create, Read, Update, Delete) automatically.

### Example: Project Form

In `my_app/components/project_form.py`:

```python
from simmate.website.data_explorer.components import TableComponent
from ..models import Project

class ProjectComponent(TableComponent):
    table = Project
    template_name = "my_app/project_form.html"
    
    # Required fields for creating a new project
    required_inputs = ["name", "description"]

    # Custom validation hook
    def check_form_hook(self):
        if len(self.form_data.get("name", "")) < 3:
            self.form_errors.append("Project name must be at least 3 characters.")
```

### Form Modes

`TableComponent` uses the `form_mode` attribute to determine its behavior. Common modes include:

-   `"create"`: Creates a new row in the database.
-   `"update"`: Updates an existing row.
-   `"search"`: Filters data based on input values.

`TableComponent` uses several attributes to determine its behavior and appearance in the Simmate Data Explorer:

-   `display_name`: A human-readable name for the table (e.g., "My Projects").
-   `description_short`: A brief description of the dataset.
-   `enabled_forms`: A list of form modes to enable (e.g., `["create", "update", "search"]`).
-   `template_names`: A dictionary mapping form modes to custom templates.

### Example: Customizing the Form

```python
class ProjectComponent(TableComponent):
    table = Project
    display_name = "Research Projects"
    description_short = "Manage your lab's computational research projects."
    enabled_forms = ["create", "update", "search"]
    
    template_names = {
        "default": "my_app/project_about.html",
        "entry": "my_app/project_view.html",
    }
```

### Permissions

By default, any logged-in user can use every enabled component type. To restrict who can create or update entries, override the `has_permission` classmethod. It receives the user, the component type (e.g. `"create"`, `"update"`, `"update_many"`), and the entry being updated (`None` for types that don't act on one existing entry).

```python
class ProjectComponent(TableComponent):
    table = Project

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        # project leaders can edit their own project
        if component_type == "update":
            return table_entry.leaders.filter(pk=user.pk).exists()
        return False
```

The check runs when the component mounts. A refused user gets a 403 and can't call any of the component's htmx actions. To hide buttons for users without permission, use the `user_can` template tag with either a table entry or a table name:

```html+django
{% user_can table_entry "update" as can_update %}
{% if can_update %}
    <a href="{% url 'data_explorer:table-entry-update' table_entry.table_name table_entry.id %}">Update</a>
{% endif %}

{% user_can "Tag" "create" as can_create_tag %}
```

--------------------------

## Component Mixins

You can extend components with pre-built mixins:

-   `UserInput`: Provides a `user_options` property to easily populate user selection boxes.
-   `MoleculeInput`: Integration with molecule sketchers.

### Example with Mixins

```python
from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

class ProjectComponent(TableComponent, UserInput):
    table = Project
    # ...
```

In your template:
```html+django
{% htmx_selectbox name="leader" options=component.user_options %}
```

--------------------------

## Advanced Backend Logic

### Triggering JS from Python

You can add actions to `self.js_actions` to trigger JavaScript on the frontend after an AJAX call.

```python
def my_method(self):
    self.js_actions.append({"type": "alert", "message": "Task completed!"})
```

### Parent-Child Communication

Use `self.retarget()` to force a parent component (or any other div) to re-render in response to a child component's action.

```python
def child_action(self):
    # Perform some logic...
    # Then tell the parent component to refresh
    return self.parent.retarget()
```
