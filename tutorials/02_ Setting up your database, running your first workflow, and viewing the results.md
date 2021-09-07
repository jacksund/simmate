This tutorial will include...
- activating conda enviornment
- exploring the simmate command and how to navigate its options
- set up your database
- viewing where the database is (.simmate folder) (intro to invisible folders/files and file extensions)
- running a workflow (is there one that doesn't require VASP? XRD maybe?)
- running the Simmate webserver
- viewing results in the web interface
- extra django commands

https://docs.djangoproject.com/en/3.2/topics/settings/#the-django-admin-utility

export DJANGO_SETTINGS_MODULE=simmate.configuration.django.settings
django-admin reset_db
django-admin graph_models -a -o image_of_models.png 
