
# Introduction to Workflows

--------------------------------------------------------------------------------

## What is a workflow?

**All workflows are really just python functions.** They can be as simple as adding two numbers together or as complex as an evolutionary search which involves hundreds of DFT calculations. Whatever the workflow may be, it needs some inputs and it then produces some result for us.

To prove this, we'll show how to make a workflow that just adds two numbers together.

--------------------------------------------------------------------------------

## A basic Python function 

Let's first create a basic python function that adds two numbers together:

```python
def add(x, y):
    return x + y

result = add(x=1, y=2)
```

Run this and you'll get `result = 3`.

Simple enough! Next, let's turn this into a Simmate workflow.

--------------------------------------------------------------------------------

### Make our first workflow

 To turn our `add` function into a Simmate workflow, we need to:

1. add the `@workflow` decorator to our function
2. make sure we include `**kwargs` as an input

Here's what our workflow looks like:

```python
from simmate.workflows import workflow

@workflow
def add(x, y, **kwargs):
    return x + y
```

And that's it! We now have a new Simmate workflow.

--------------------------------------------------------------------------------

## Running our workflow

Note how we originally ran our python function with this:
``` python
result = add(x=1, y=2)
```

This code won't work anymore, because we've now changed our function into a `Workflow`. From earlier tutorials, we learned that workflows must be called with `.run()` instead. Therefore our code becomes:

``` python
status = add.run(x=1, y=2)
result = status.result()
```

!!! note
    Our workflow run returned a `status` instead of our `result`. This is because (in advanced cases) we will be *submitting* workflows to a cluster, rather than running them directly. In such cases, it is common to submit workflow runs and check the result later.

    This will be covered in the final Simmate tutorial on `Computational Resources`.

And here is our final script:

```python
from simmate.workflows import workflow

@workflow
def add(x, y, **kwargs):
    return x + y

status = add.run(x=1, y=2)
result = status.result()
```

Just like with our original function, we should see `result = 3`.

--------------------------------------------------------------------------------

## What changed?

So far, this might seem like a lot of work (and complexity) just to get the same result. But let's look under the hood and see the basics of what has changed.

### Extra parameters

For starters, we added `**kwargs`. Let's modify our function to see what this actual did:

```python
from simmate.workflows import workflow

@workflow
def add(x, y, **kwargs):
    print(f"Extra kwargs: {kwargs}")  # add this new line!!!
    return x + y

status = add.run(x=1, y=2)
result = status.result()
```

When we run this again, we will see a print statement will output something similar to this: 

```
Extra kwargs: {
    'run_id': 'eb467f3e-eb27-4bd0-8600-c49757bc5b63',
    'directory': Path('path/to/simmate-task-abcd1234'),
    'compress_output': False,
    'source': None,
    'started_at': datetime.datetime(...),
}
```

What happened is that Simmate performed some extra setup for us. This included things such as...

- creating a unique workflow id (to help identify things in the database)
- creating a new folder (`directory`) that the workflow can use as a scratch space
- compressing the final folder to a `.zip` file (if requested)
- ... and more!

### Extra properties & methods

Because we now have a Simmate workflow, we can also access new properties and methods. For example:

``` python
# run one line at a time

add.name_full

add.show_parameters()
```

### ... and more

With this workflow, there are also advanced features we can include. This can be thing such as...

- advanced parameter loading
- saving the `result` to a database
- saving calculation info (like total time) to a database
- viewing & running the workflow in the website interface

Features like these (and more), are covered in later tutorials as well as the Full Guides section.

--------------------------------------------------------------------------------
