# -*- coding: utf-8 -*-

import asyncio


def async_to_sync(to_await):
    """
    decorator that converts an async function to a sync function

    If using on a classmethod or property, have this at the bottom. For example:

    ```python
    class Test:

        @classmethod
        @property
        @async_to_sync
        async def some_method(cls):
            <then your async code>
    ```
    """

    # This is a hack from several stack overflow posts combined and turned into
    # a decorator...
    #   https://stackoverflow.com/questions/55647753/
    #   https://stackoverflow.com/questions/56154176/
    #   https://realpython.com/primer-on-python-decorators/
    # I have no clue what's going on but this decorator works. Soooo who cares.
    # But I should really figure out how to call async functions with regular
    # ones, or ask Prefect how to use their client within methods...

    def wrapper(*args, **kwargs):
        async_response = []

        async def run_and_capture_result():
            r = await to_await(*args, **kwargs)
            async_response.append(r)

        loop = asyncio.get_event_loop()
        coroutine = run_and_capture_result()
        loop.run_until_complete(coroutine)
        return async_response[0]

    return wrapper


# This checks if there's an active async loop -- which will be the case if
# we are within an ipython console (like in Spyder or Jupyter notebooks).
# If not, there is a normal async_to_sync that we can use.
try:
    loop = asyncio.get_running_loop()  # will fail no loop is available

    # HERE --> we are in Spyder or an ipython terminal

    import nest_asyncio

    nest_asyncio.apply()

except RuntimeError:
    # HERE --> we are not in Spyder or an ipython terminal

    # When possible, we'd like to switch to the django-recommended decorator,
    # it's use is more robust and ensures best practices.
    # https://docs.djangoproject.com/en/4.0/topics/async/#async-adapter-functions

    from asgiref.sync import async_to_sync
