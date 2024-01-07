# Constructing Custom Database Tables and Applications

-------------------------------------------------------------------------------

## When to Create a Simmate Project?

A custom Simmate project is necessary if you wish to construct a new database table or access your workflows via the website interface.

There are several other reasons to create a project, such as:

- [x] Utilizing a custom database table to store workflow results
- [x] Accessing the workflow through the website interface
- [x] Accessing the workflow from other scripts (and the `get_workflow` function)
- [x] Organizing code into smaller files for easy import
- [x] Sharing workflows within a team
- [x] Allowing others to install your workflows after publishing a new paper

All these tasks can be accomplished using Simmate "projects". Essentially, these projects are folders containing Python files arranged in a specific format (i.e., there are rules for file naming and content).

-------------------------------------------------------------------------------

## Is this Equivalent to Creating a New Package?

Yes, indeed -- Projects are essentially the creation of a new Python package. In fact, our `start-project` command functions like a "cookie-cutter" template.

This has significant implications for code and research sharing. With a fully-functional and published Simmate project, you can share your code with other labs via Github and PyPi. This allows the entire Simmate community to install and use your custom workflows with Simmate. For them, the process is as simple as:

1.  `pip install my_new_project`
2.  Adding `example_app.apps.ExampleAppConfig` to their `~/simmate/my_env-apps.yaml`

Alternatively, you can request to merge your app into our Simmate repository, making it a default installation for all users. Whichever path you choose, your hard work will be more accessible to the community and new users!

-------------------------------------------------------------------------------