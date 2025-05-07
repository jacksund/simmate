
## What are web components?

**Components let you build interactive web pages using Python and HTML**, without needing JavaScript (we handle that part for you). So components work like mini Django views that automatically update when users interact with them.

We need components because Django views are static HTML by default. In other words, once your view+template is loaded, it does not change until you (i) open a new link or (ii) refresh your page. So components come into play when you want to click a button and have the web page altered in some way -- such as checking a box and then having extra form options show up. For this, our HTML needs to include some JavaScript that updates the page for us -- all without refreshing the web page. Simmate web components integrate this JavaScript+AJAX calls, so that you can build things out in Python instead. This enables real-time interactivity in our web pages.

--------------------------

## Do I need components?

Avoid overcomplicating things if you can. You can achieve quite a bit just with static HTML that ships with Django, and the only time you need components are when you have...

- a dynamic submission form (e.g., one that changes as a user fills it out)
- a need for real-time data analytics (e.g., manually refreshing your webpage isn't cutting it)

Even if this applies to you, make sure you are already comfortable with HTML and [`Django Templates`](https://docs.djangoproject.com/en/5.2/topics/templates/) before messing with components.

!!! tip
    A beginner-friendly alternative for building dynamic web pages is [Streamlit](https://streamlit.io/). You can then make the app available within your Simmate app using an `iframe`:
    ``` html
    <iframe src="{{ dashboard_url }}?embed=true"
            style="height:150vh;
                   width:100%;
                   border:none">
    </iframe>
    ```

--------------------------

## Django-Unicorn vs. Simmate

Simmate originally used [Django-Unicorn](https://www.django-unicorn.com/) to build out interactive pages. However, in order to address some of our use cases and loose bugs, we eventually forked & refactored their codebase -- and now maintain our [own internal copy](https://github.com/jacksund/simmate/tree/main/src/simmate/website/unicorn). Still, nearly all features from Django-Unicorn's [examples](https://www.django-unicorn.com/examples/todo) and [documentation](https://www.django-unicorn.com/docs/) are still available.

--------------------------

## Basic Example

In your app, you can set up the following:
```
├── example_app
│   ├── components
│   │   ├── __init__.py
│   │   └── todo.py
│   ├── templates
│   │   ├── unicorn
│   │   │   └── todo.html
│   │   └── my_homepage.html
│   ├── urls.py
│   └── views.py
```

And for each file & it's contents:


=== "urls.py"
    ``` python
    from django.urls import path
    from . import views
    
    urlpatterns = [
        path('', views.home, name='home'),
    ]
    ```

=== "views.py"
    ``` python
    from django.shortcuts import render
    
    def home(request):
        context = {"name": "Jane Doe"}
        return render(request, "my_homepage.html", context)
    ```

=== "todo.py"
    ``` python
    from simmate.website.core_components.components import DynamicFormComponent
    
    
    class TodoView(UnicornView):
        task = ""
        tasks = []
    
        def add(self):
            self.tasks.append(self.task)
            self.task = ""
    ```

=== "my_homepage.html"
    ``` html
    <!DOCTYPE html>
    <html>
        <head>
            <title>Home Page</title>
        </head>
        <body>
            <h1>Hello, {{ name }}! This is the home page rendered from a template.</h1>
            <div>
                {% load unicorn %}
                {% unicorn 'todo' %}
            </div>
        </body>
    </html>
    ```

=== "todo.html"
    ``` html
    <div>
        <form unicorn:submit.prevent="add">
            <input type="text" unicorn:model.lazy="task" placeholder="New task" id="task"></input>
        </form>
        <button unicorn:click="add">Add</button>
        <p>
            {% if tasks %}
                <ul>
                    {% for task in tasks %}
                        <li>{{ task }}</li>
                    {% endfor %}
                </ul>
                <button unicorn:click="$reset">Clear all tasks</button>
            {% else %}
                No tasks!
            {% endif %}
        </p>
    </div>
    ```

--------------------------

## Page Elements

- `frontend` --> `html (+js)`
- `backend` --> `python`

``` html
{% load simmate_ui_tags %}
```

### text_input

=== "frontend"

    ``` html
    {% text_input name="example" %}
    ```

=== "backend"

    ``` python
    example = "some default text"
    ```

### text_area

=== "frontend"

    ``` html
    {% text_area name="example" %}
    ```

=== "backend"

    ``` python
    example = "some default text"
    ```

### number_input

=== "frontend"

    ``` html
    {% number_input name="example" %}
    ```

=== "backend"

    ``` python
    example = 123
    ```

### checkbox

=== "frontend"

    ``` html
    {% checkbox name="example" %}
    ```

=== "backend"

    ``` python
    example = True
    ```

### button

=== "frontend"

    ``` html
    {% button name="example" %}
    ```

=== "backend"

    ``` python
    def example(self):
        # ... any python code 
    ```

### selectbox

=== "frontend"

    ``` html
    {% selectbox name="example" %}
    ```

=== "backend"

    ``` python
    example = None
    example_options = [
        ("label 1", "value 1"),
        ("label 2", "value 2"),
        ("label 3", "value 3"),
        # ...
    ]
    ```

### radio

=== "frontend"

    ``` html
    {% radio name="example" %}
    ```

=== "backend"

    ``` python
    example = None
    example_options = [
        ("label 1", "value 1"),
        ("label 2", "value 2"),
        ("label 3", "value 3"),
        # ...
    ]
    ```

### molecule_input

=== "frontend"

    ``` html
    {% molecule_input %}
    ```

=== "backend"

    ``` python
    from simmate.website.core_components.components import (
        DynamicFormComponent,
        MoleculeInput,
    )


    class CortevaTargetFormView(DynamicFormComponent, MoleculeInput):

        class Meta:
            javascript_exclude = (
                # ...
                *DynamicFormComponent.Meta.javascript_exclude,
                *MoleculeInput.Meta.javascript_exclude,
            )
    ```

search_box
alert
draw_molecule
canvas


## Backend Mix-ins

#### test 1

#### test 2