# -*- coding: utf-8 -*-

"""
This defines the command for starting new custom project.
"""

import click


@click.command()
@click.argument(
    "project_name",
    type=click.Path(exists=False),
)
def start_project(project_name):
    """
    This creates a new folder and fills it with an example project to
    get you started with custom simmate code.
    """

    import os
    from django.core.management import call_command
    from simmate import configuration  # needed just for the filepath

    # This directory is where our template folder is located. We find this
    # by looking at the import path to see where python installed it.
    config_directory = os.path.dirname(os.path.abspath(configuration.__file__))

    # We add on "project_template" to this file path as that's our full template
    template_directory = os.path.join(config_directory, "example_project")

    # we now make the project folder using our template directory.
    # Note, we are using Django's "startproject" command even though we are just
    # copying files over. This might be overkill but it gets the job done.
    call_command("startproject", project_name, template=template_directory)

    # grab the full path to the new project for the user to see
    new_project_directory = os.path.join(os.getcwd(), project_name)

    # also navigate to the user's ~/simmate/applications.yaml file and we
    # want to add a new line at the end of it (or create the file if it isn't
    # there yet)
    from pathlib import Path

    apps_yaml = os.path.join(Path.home(), "simmate", "applications.yaml")
    new_line = "\nexample_app.apps.ExampleAppConfig"  # \n ensures a new line

    # If the file exists, we append this line to the end of the file. Otherwise,
    # we create a new file and add the line!
    with open(apps_yaml, "a+") as file:
        file.write(new_line)
    # Let the user know what we did and how to continue.
    click.echo(
        f"\n\tSuccessfully made a new project! You'll find it at {new_project_directory}\n\n"
        "\tBe sure to go through the README file in your new project.\n"
    )


# explicitly list functions so that pdoc doesn't skip them
__all__ = ["start_project"]
