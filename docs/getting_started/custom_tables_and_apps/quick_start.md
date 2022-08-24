
# Build custom database tables and apps

> :warning: There is no "quick tutorial" for this topic. Even advanced users should read everything!

In this tutorial, you will learn how to build customized database table and also learn how to build out your customized features into "projects" (or "apps").


## Should I create a Simmate project?

Whether you're a beginner or expert, building a big project or small one: the answer is 100% yes. :fire::fire::rocket:

At the end of the last tutorial, we posed a number of ideas. What if we wanted to...

- use a custom database table to save our workflow results
- access the workflow in the website interface
- access our workflow from other scripts (and the `get_workflow` function)

On top of these, we might also want to...

- share workflows among a team
- let others install your workflows after you publish a new paper

All of these can be done using Simmate "projects". These projects are really just a folder of python files in a specific format (i.e. we have rules for naming files and what to put in them).

## Is this just creating a new package?

For expert python users, you will notice that projects are indeed building a new python package. In fact, our "start-project" command is really just a cookie-cutter template! This can have huge implications for sharing research and code. With a fully-functional and published Simmate project (or "app"), you can upload your project for other labs to use via Github and PyPi! Then the entire Simmate community can install and use your custom workflows with Simmate. For them, it'd be as easy as doing

1.  `pip install my_new_project`
2.  adding `example_app.apps.ExampleAppConfig` to their `~/simmate/applications.yaml`


Alternatively, you can request that your app be merged into our Simmate repository, so that it is installed by default for all users. Whichever route you choose, your hard work should be much more accessible to the community and new users!

> :bulb: In the future, we hope to have a page that lists off apps available for download, but because Simmate is brand new, there currently aren't any existing apps outside of Simmate itself. Reach out to our team if you're interested in kickstarting a downloads page!
