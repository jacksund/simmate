
# Installation

In this tutorial, you will learn how to install Simmate with Anaconda and start up a local server. Beginners will also be introduced to the command-line.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [A quick python dictionary](#a-quick-python-dictionary)
    - [Why Anaconda?](#why-anaconda)
    - [Installing Anaconda and a first look](#installing-anaconda-and-a-first-look)
    - [Switching to the Command-line](#switching-to-the-command-line)
    - [Creating our environment and installing Simmate](#creating-our-environment-and-installing-simmate)
    - [Exploring Simmate's command-line](#exploring-simmates-command-line)
    - [Starting your local test server](#starting-your-local-test-server)
    - [Extra Resources](#extra-resources)

<br/><br/>

# The quick tutorial

> :warning: In this tutorial and others, beginners should skip the **quick tutorial** section and jump straight to the **full tutorial**. The critical steps in each are exactly the same, but the full tutorial includes extra exploration of the software and how to use it. So be sure to read the full tutorials if you don't have coding experience!

> :bulb: Simmate itself is <2MB, but when installed to a clean conda environment, the entire download for Simmate and all it's dependencies comes to ~1.2GB. Additional disk space is also needed for optional downloads -- such as [third-party data](https://jacksund.github.io/simmate/simmate/database/third_parties.html).

1. Install [anaconda](https://www.anaconda.com/products/distribution)
2. Create a conda environment, install Simmate in it, and activate it. *(note: Spyder is our recommended IDE but optional)*
``` shell
conda create -n my_env -c conda-forge python=3.10 simmate
conda install -n my_env -c conda-forge spyder  # optional but recommended
conda activate my_env
```
3. Run the `simmate` command to make sure it's installed correctly
4. For first-time setup, initialize your local database with `simmate database reset`
5. Run the command `simmate run-server` (and leave this command running)
6. Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and you'll see you local server!

Note, this server is only accessible on your local computer. For a production-ready server, see our [website documentation](https://jacksund.github.io/simmate/simmate/website.html#running-a-production-ready-server).

<br/><br/>

# The full tutorial

<br/>

## A quick python dictionary

As you read through our tutorials, we try to explain many of the python terms and concepts, but for your reference, we have written out some quick definitions here. You won't be expected to understand all of these terms until tutorial 06, so revisit these definitions after each tutorial to review your understanding.

- `package`: a package is, essentially, a software program written in python.  Simmate is a package.
- `package manager`: this manages the installation of python and its packages.  It automatically installs the correct version of packages to ensure that different packages are compatible with each other. Anaconda is our package manager.
- `channel`: python packages are downloaded from a specific channel on the internet. For Simmate, we tell Anaconda to use conda-forge as its main channel.
- `environment`: python packages are installed into a specific environment on your computer. An environment is (effectively) a folder containing many installed packages that are each compatible each other. A single computer can have many environments, where you only ever use one at a time.  In this tutorial, "my_env" is the name of our environment and Simmate is installed in it (along with many other packages such as pymatgen).
- `module`: A python package is made from modules.  Each module provides a related set of functions. For example, "simmate.database" is a module that holds all of the code used to run our database.
- `IDE`: the program we write and run python code in. Microsoft Word would be an IDE for writing essays. Spyder is our IDE for python. IDE is short for integrated development environment.

Also, don't confuse two types of programming language we will use:

- `command-line`: Whether you are on Windows, Mac, or Linux, the command line (aka the terminal) is used for common functions like changing directories (cd Desktop) or running programs. This includes running python modules, such as: "simmate workflows run".
- `python`: used when we write complex logic and customize its settings. "workflow.run(structure=...)" is python code used in our IDE.

<br/>

## Why Anaconda?

Ideally, you could download Simmate like any desktop app and then be good to go. But have you ever updated your operating system and then everything else on your computer goes haywire? With python, the chances of that happening are extremely high, so we want to be careful. For example, say I wanted two packages installed:

1. Simmate version 1.0, which requires python version 3.10 or greater
2. Numpy version 1.15, which requires python version 2.7

The conflicting versions of python creates a problem. To solve this, we use [Anaconda](https://www.anaconda.com/products/). Anaconda installs python and all of our extra packages, including Simmate. To make sure nothing ever breaks, it separates each of our installations into folders known as "environments". So using our example programs, we could have two environments: one named "simmate_env" and another named "numpy_env" (these can be named anything). The two different python versions and codes would be installed into separate folders so that they don't interact.

Package versions can also conflict with each other. For example, Simmate requires the package Django (version >3.2), so if you installed Django 2.0, it would break your Simmate installation. Therefore, Anaconda prevents you from installing conflicting versions within a single environment.

<br/>

## Installing Anaconda and a first look

For this tutorial, we'll install Anaconda to your local desktop/laptop. Even if you'll be using a university supercomputer (or some other remote computer system) to run workflows, stick to your local computer. We'll switch to your remote supercomputer near the end of tutorial 02.

To install Anaconda, you don't need to make an account on their website. Just use [their download page](https://www.anaconda.com/products/distribution) and install Anaconda (individual edition). Use all of the default options when installing. Open the application when you're done! The application will be called "Anaconda Navigator".

On the homescreen, you'll see several IDEs, such as Orange3, Jupyter Notebook, Spyder, and others. These IDEs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, LibreOffice, and others for writing papers, all of these IDEs are different ways to write python. Our prefered IDE is [Spyder](https://www.spyder-ide.org/), which we will introduce in tutorial 03.

<!-- This is an image of the Anaconda GUI home -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-defaults.png"  height=440 style="max-height: 440px;">
</p>

On the left, you'll see an "Environments" tab. Go ahead and open it. When you first install Anaconda, there will only be a "base" environment that already has popular packages installed. You can create new environments here and install new packages into each -- all without affecting what's already installed.

<!-- This is an image of the Anaconda GUI environments -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-env1.png"  height=440 style="max-height: 440px;">
</p>

That's really it to the Anaconda interface! While we can install Simmate with this interface, it's actually even easier with the command-line. The remainder of this tutorial will use the command-line instead of the Anaconda Navigator interface.

If you want a more complete overview of Anaconda, they have a series of [getting-started guides](https://docs.anaconda.com/anaconda/user-guide/) available, but these guides aren't required for using Simmate (so don't spend any more than 10 minutes looking through them).

<br/>

## Switching to the Command-line

While the Anaconda Navigator interface is convenient if you've never written code before, it is much quicker (and easier!) to use the command-line. Don't worry, it's much simpler than you probably expect. Even if you don't know how to code, you can master the command-line in just a few minutes.

Each command can be viewed as a "button". For example, the command `cd` stands for "change directory". When you call it, it just opens up a new folder to view the contents -- so the same thing as double-clicking a folder to open it up!

Let's try this out with our command-line.

- On Windows, search for and open "Anaconda Powershell Prompt" using your Start menu.
- On Mac and Linux, search for and open the app named "Terminal"

You should see something like this:

<!-- This is an image of an empty terminal with anaconda installed -->
<p align="center" style="margin-bottom:40px;">
<img src="https://aws1.discourse-cdn.com/codecademy/original/5X/0/4/8/7/0487a63480b3b9cd0fc056877d8abaa2b1e90e3d.png"  height=330 style="max-height: 330px;">
</p>

You'll see `(base)` at the start of the line. This is our anaconda enviornment that we are currently using. After that, you'll see the "current working directory", which is the folder we currently have open and are sitting in. On Windows this will be your user folder (e.g. `C:\Users\jacksund`) and for Mac/Linux you'll see `~` which is shorthand for your user folder (e.g. `home/jacksund`).

Now, try typing in the command `cd Desktop` and then hit enter. This will open up your Desktop folder. Then enter the command `ls`, which will list all files and folders on your Desktop. 

``` shell
# run these two commands
cd Desktop
ls
```

For other simple commands, you can take a look at [this cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) or take [a full tutorial](https://www.codecademy.com/learn/learn-the-command-line). Memorizing commands will come slowly over time, so keep this cheat-sheet handy. We highly recommend that you spend 30 minutes going through these links once you finish this tutorial.

Obviously, the tricky part with the command-line is knowing what to type. Fortunately, however, most programs have a single command that forms the base of more complex commands. For anaconda, the command is `conda`. If you aren't sure what it does or how to use it, you just add `--help` to it. Type in the command `conda --help` and you'll see an output like this:

``` shell
conda --help
```

``` shell
usage: conda [-h] [-V] command ...

conda is a tool for managing and deploying applications, environments and packages.

<< TO SAVE SPACE FOR THE TUTORIAL, WE REMOVED THE REST OF THE OUTPUT >>
```

Don't get overwhelmed by the amount of information printed out. Each line is getting accross a simple idea. 

For example, the line `-h, --help     Show this help message and exit.` is telling us what the `conda --help` command does! It also tells us that we could have done `conda -h` for the same output.

This help message also tells us there are other "subcommands" available. One is `create` which says it creates a new environment. To learn more about that one, we can run the command `conda create --help`. There's a bunch here... But again, you don't need to memorize all of this. Just remember how to get this help page when you need it. Up next, we'll use these commands to create our environment and install Simmate.

<br/>

## Creating our environment and installing Simmate

For now, let's create a new environment that uses the [conda-forge](https://conda-forge.org/) channel. A channel is where anaconda downloads packages from -- and to keep things simple, we will ALWAYS use conda-forge (this is the standard in the python community). Now let's run this command below. Note you can switch out the name "my_env" for whatever you want here, just make sure you use underscores instead of spaces ("my_env" will work while "my env" will give an error).

``` shell
conda create -c conda-forge -n my_env python=3.10
```

Say yes when the installation asks for confirmation. Next, switch to this new environment. To do that we use...

``` shell
conda activate my_env
```

You'll see the start of your command line switch from `(base)` to `(my_env)` if this worked successfully. Next, we want to install Simmate.

``` shell
conda install -c conda-forge -n my_env simmate
```

This may take a few minutes to run and install. But once it's done, you've now successfully installed Simmate! If you ran into any errors with this very last command, please let our team know immediately by [posting a new issue here](https://github.com/jacksund/simmate/issues/).

As an extra, let's use Anaconda to install [Spyder](https://www.spyder-ide.org/). Spyder is what we will use to write python in later tutorials. But now that we have Anaconda set up, installing new programs can be done in just one line:
``` shell
conda install -c conda-forge -n my_env spyder
```

<br/>

## Exploring Simmate's command-line

Just like we used `conda --help` above, we can also ask for help with Simmate. Start with running the command `simmate --help` and you should see the following output:

``` shell
simmate --help
```

```
Usage: simmate [OPTIONS] COMMAND [ARGS]...

  This is the base command that all others stem from.

  If you are a beginner to the command line, be sure to start with our
  tutorials: https://github.com/jacksund/simmate/tree/main/tutorials

  Below you will see a list of sub-commands to try. For example, you can run
  `simmate database --help` to learn more about it.

Options:
  --help  Show this message and exit.

Commands:
  database         A group of commands for managing your database.
  run-server       This runs a website test server locally for Simmate.
  start-project    This creates a new folder and fills it with an example...
  workflow-engine  A group of commands for starting up Prefect Agents and...
  workflows        A group of commands for running workflows or viewing...
```

You can see there are many other commands like `simmate database` and `simmate workflows` that we will explore in other tutorials. 

<br/>

## Starting your local test server

On our official website, you are able to explore all results from past workflows that we've ran. Even though you haven't ran any yet, you can do the same thing on your local computer too. All that's required are two simple commands.

First, we need to setup our database. We'll explain what this is doing in the next tutorial, but for now, think of this as building an empty excel spreadsheet that we can later fill with data. This is done with...

``` bash
# Confirm that you want to reset/delete your "old" database when prompted.
# Also agree to download and use a prebuilt database.
simmate database reset
```

> :bulb: Unless you want to remove all of your data and start from scratch, you'll never have to run that command again.

And then as our second step, we simply tell Simmate to start the server:

``` bash
simmate run-server
```

... and after a few seconds, you should see the output ...

``` bash
Watching for file changes with StatReloader
April 05, 2022 - 00:06:54
Django version 4.0.2, using settings 'simmate.configuration.django.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Leave this command running in your terminal and open up the link [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your preferred browser (Chrome, Firefox, etc.). You should see what looks like the simmate.org website! This website, however, is running on your local computer and won't contain any data yet. No one can access it outside of your own computer, and as soon as your close your terminal running the `simmate run-server`, this site will stop working too.

If you reaaally wanted to, you could stop going through our tutorials and just interact with your local server. But where Simmate becomes especially powerful is when we switch to a server that accessible through the internet -- that way, you can share results and computational resources with your entire team. To do this, you'll have to keep reading our tutorials! 

Additionally, an important thing to keep in mind is that Simmate is MUCH more powerful when you start interacting with our code -- rather than just using the web interface. By learning to interact with Simmate's code using the command-line and Python, you can quickly submit 1000s of calculations and access advanced functionality that isn't yet available in the interface (and there's a lot of it). Keep this in mind as you continue through our other tutorials! We'll teach you how to interact with our code so that you can take full advantage of Simmate.

As a final note, spend some time with the extra resources (below) and then continue on to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md) where we'll learn how to run workflows.

<br/>

## Extra Resources

- [Anconda's getting-started guides](https://docs.anaconda.com/anaconda/user-guide/) (we recommend taking ~10min to glance through)
- [A command-line cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) (useful printout to have at your desk)
- [A full tutorial for the command-line](https://www.codecademy.com/learn/learn-the-command-line) (we HIGHLY recommended parts 1 and 2, which will take 1-2 hours)

*All tutorials that we recommend from codecademy.com can be completed before your free trial expires.*
