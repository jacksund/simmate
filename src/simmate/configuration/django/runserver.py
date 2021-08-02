# -*- coding: utf-8 -*-

def runserver():

    # for now I recommend using the shell command...
    #   "django-admin runserver --setting=simmate.configuration.django.settings"
    raise NotImplementedError

    # BUG: I'm not sure why this code below doesn't work...
    # execute the following command to run the server
    # from django.core.management import call_command
    # call_command('runserver')

    # BUG: this code sorta works... but I'm not able to kill the server once
    # it's launched - even with .terminate() and restarting spyder
    #
    # grab the working directory
    # wait=False, timeout=300
    # from simmate.settings import BASE_DIR
    # from subprocess import Popen
    # # and now submit the command via a separate shell
    # future = Popen(
    #     "python manage.py runserver",
    #     cwd=BASE_DIR,
    #     shell=True,
    # )
    # # see if we want to wait until the command completes or not
    # if wait:
    #     future.wait(timeout=timeout)
    #     # kill the task after the timeout
    #     future.terminate()
    # # return the future if the user wants it
    # return future
