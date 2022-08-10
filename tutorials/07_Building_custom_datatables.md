
# Building custom workflows

> :warning: There is no "quick tutorial" for this topic. Even advanced users should read everything!

In this tutorial, you will learn how to build customized database table and also learn how to build out your customized features into "apps".

1. [ Simmate projects and why to make them](#simmate-projects-and-why-to-make-them)
2. [Creating a Project for our custom features](#creating-a-project-for-our-custom-features)

</br>

## Simmate projects and why to make them

At the end of the last tutorial, we posed a number of position ideas. What if we wanted to...
- use a custom database to save our workflow results
- access the workflow in the website interface
- access our workflow from other scripts (and the `get_workflow` function)

On top of these, we might also want to...
- share workflows among a team
- let others install your workflows after you publish a new paper
- 

</br>

## Creating a Project for our custom features



In 

1. Let's create a project named `my_new_project`. To do this, navigate to a folder where you'd like to store your code and run...

``` bash
simmate start-project my_new_project
```

2. You will see a new folder named "my_new_project" which you can switch into.

``` bash
cd my_new_project
```

3. Open up the `README.md` file in this folder and read through our directions. If you want a web-form of this guide, use [this link](https://github.com/jacksund/simmate/tree/main/src/simmate/configuration/example_project)

4. After completing the steps in that readme, you've now registered your workflow and database tables to simmate!


For expert python users, you may notice that you are building the start of a new python package here. In fact our "start-project" command is really just a cookie-cutter template! This can have huge implications for sharing research and code. With a fully-functional and published Simmate app, you can upload your project for other labs to use via github and PyPi! Then the entire Simmate community can install and use your custom workflows with Simmate. For them, it'd be as easy as doing (i) `pip install my_new_project` and (ii) adding `example_app.apps.ExampleAppConfig` to their `~/simmate/applications.yaml`. Alternatively, you can request that your app be merged into our Simmate repository, so that it is installed by default for all users. Whichever route you choose, your hard work should be much more accessible to the community and new users!

> :warning: In the future, we hope to have a page that lists off apps available for download, but because Simmate is brand new, there currently aren't any existing apps outside of Simmate itself. Reach out to our team if you're interesting in kickstarting a downloads page!

Up next, we will start sharing results with others! Continue to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/08_Use_a_cloud_database.md) when you're ready.
