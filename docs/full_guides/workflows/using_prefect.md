# Prefect Backend (Experimental)

When you choose Prefect as your workflow executor, Workflows are internally converted into Prefect Flows. This makes understanding Prefect beneficial for handling complex scenarios. For advanced usage or when developing new features, we recommend going through the Prefect tutorials available [here](https://orion-docs.prefect.io/tutorials/first-steps/).

## Minimal Example (Prefect vs. Simmate)

It's useful to understand the comparison between Prefect and Simmate workflows. For simple scenarios involving Python code, a Prefect workflow is defined as follows:

``` python
from prefect import flow

@flow
def my_favorite_workflow():
    print("This workflow doesn't do much")
    return 42

# Execute your workflow
state = my_favorite_workflow()
result = state.result()
```

To convert this into a Simmate workflow, we only need to slightly adjust the format. Instead of using a `@flow` decorator, we use the `run_config` method of a new subclass:

``` python
# NOTE: This example does not follow Simmate's naming convention, 
# which may cause some higher-level features to not function correctly. This will be corrected in a subsequent step.

from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

# Execute your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Internally, the `run` method converts our `run_config` into a Prefect workflow. Methods like `run_cloud` will now automatically use Prefect.