
## Django vs. Simmate

Simmate does not do anything special with views -- we just use the [Django web framework](https://www.djangoproject.com/). So you can follow [Django's official guides](https://docs.djangoproject.com/en/5.2/topics/http/) on how to create web views, urls, and templates.


## Basic Example

In your app, you can set up the following:
```
├── example_app
│   ├── templates
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

=== "my_homepage.html"
    ``` html
    <!DOCTYPE html>
    <html>
        <head>
            <title>Home Page</title>
        </head>
        <body>
            <h1>Hello, {{ name }}! This is the home page rendered from a template.</h1>
        </body>
    </html>
    ```


To view this in the website:

1. Make sure your app is [registered with Simmate](/full_guides/apps/creating_custom_apps.md#register-your-app).
2. Navigate to the `Apps` tab in the website and you should see your app listed
3. Select your `Apps` and it will open the `""` path (homepage) in your app's `urls.py`

!!! example
    If your app was called `example_app` and this was your `urls.py`:

    ``` python
    from django.urls import path

    from . import views

    urlpatterns = [
        path('', views.index, name='index'),
        path('my-custom-view/', views.my_custom_view, name='custom'),
    ]
    ```

    You could view them in the Simmate website at:

    - `http://127.0.0.1:8000/apps/example_app/`
    - `http://127.0.0.1:8000/apps/example_app/my-custom-view/`


## How views are registered

Normally in Django, you have a main `urls.py` and you register apps to it like so:

``` python
from django.urls import include, path

urlpatterns = [
    # ...
    path("example/", include("example_app.urls")),
    # ...
]
```

In Simmate, we have our own `urls.py` file, and we automatically add your app to it. Everything in your `urls.py` will be mapped to a namespace matching your app's name using:

``` python
path(
    route=f"apps/{APP_NAME}/",
    view=include((path_to_urls_file, APP_NAME), namespace=APP_NAME),
    name=APP_NAME,
),
```
