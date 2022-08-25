
# Prefect backend (experimental)

When you enable Prefect as your workflow executor, Workflows are converted into
Prefect Flows under the hood, so having knowledge of Prefect can be useful in 
advanced cases. For advanced use or when building new features, we recommend 
going through the prefect tutorials located
[here](https://orion-docs.prefect.io/tutorials/first-steps/).


## Minimal example (Prefect vs. Simmate)

It's useful to know how Prefect workflows compare to Simmate workflows. For
simple cases where you have python code, you'd define a Prefect workflow
like so:

``` python
from prefect import flow

@flow
def my_favorite_workflow():
    print("This workflow doesn't do much")
    return 42

# and then run your workflow
state = my_favorite_workflow()
result = state.result()
```

To convert this to a Simmate workflow, we just need to change the format
a little. Instead of a `@flow` decorator, we use the `run_config` method
of a new subclass:

``` python
# NOTE: this example does not follow Simmate's naming convention, so
# some higher level features will be broken. We will fix in a later step.

from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

# and then run your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Behind the scenes, the `run` method is converting our `run_config` to a
Prefect workflow for us. Methods like `run_cloud` will automatically use
Prefect now too.
