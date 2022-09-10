
# Build custom database tables and apps

In this tutorial, you will learn how to build customized database table and also learn how to build out your customized features into a "project" and "apps".

!!! note
    There is no "quick tutorial" for this topic. Even advanced users should read everything.

-------------------------------------------------------------------------------

## Should you create a Simmate project?

A custom Simmate project is required if you want to build a new database table or access your workflows in the website interface.

There are many more reasons you'd want to create a project. This includes wanting to...

- [x] use a custom database table to save our workflow results
- [x] access the workflow in the website interface
- [x] access our workflow from other scripts (and the `get_workflow` function)
- [x] begin organizing our code into smaller files and easily import them
- [x] share workflows among a team
- [x] let others install your workflows after you publish a new paper

All of these can be done using Simmate "projects". These projects are really just a folder of python files in a specific format (i.e. we have rules for naming files and what to put in them).

-------------------------------------------------------------------------------

## Is this just creating a new package?

Yep -- Projects are indeed building a new python package. In fact, our `start-project` command acts just like a "cookie-cutter" template.

This can have huge implications for sharing research and code. With a fully-functional and published Simmate project, you can upload your code for other labs to use via Github and PyPi. Then the entire Simmate community can install and use your custom workflows with Simmate. For them, it'd be as easy as doing

1.  `pip install my_new_project`
2.  adding `example_app.apps.ExampleAppConfig` to their `~/simmate/my_env-apps.yaml`


Alternatively, you can request that your app be merged into our Simmate repository, so that it is installed by default for all users. Whichever route you choose, your hard work should be much more accessible to the community and new users!

!!! note 
    In the future, we hope to have a page that lists off apps available for download, but because Simmate is brand new, there currently aren't any existing apps outside of Simmate itself. Reach out to our team if you're interested in kickstarting a downloads page!

-------------------------------------------------------------------------------
