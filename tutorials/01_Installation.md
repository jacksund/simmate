# Installation

In this tutorial, you will learn how to install Simmate with Anaconda. Beginners will also be introduced to the command-line.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [Why Anaconda?](#why-anaconda)
    - [Installing Anaconda and a first look](#installing-anaconda-and-a-first-look)
    - [Switching to the Command-line](#switching-to-the-command-line)
    - [Creating our environment and installing Simmate](#creating-our-environment-and-installing-simmate)
    - [Exploring Simmate's command-line](#exploring-simmates-command-line)
    - [Extra Resources](#extra-resources)

<br/><br/>
# The quick tutorial

1. Install [anaconda](https://www.anaconda.com/products/individual-d)
2. Create a conda enviornment, install Simmate in it, and activate it. *(note: Spyder is our recommended IDE but optional)*
```
conda create -n my_env -c conda-forge python=3.8 simmate spyder
conda activate my_env
```
3. Run the `simmate` command to make sure it's installed correctly

<br/><br/>
# The full tutorial

## Why Anaconda?

Ideally, you could download Simmate like any desktop app and then you'd be good to go. But have you ever installed a new program and then everything else on your computer goes haywire? With python, the chances of that happening are extremely high, so we want to be careful. For example, say I wanted two programs installed:

1. Simmate, which requires Python version 3.8 or greater
2. Another old program, which requires Python version 2.6 exactly

The conflicting python versions would give issues here. To overcome this, we use [Anaconda](https://www.anaconda.com/products/individual-d). Anaconda installs Python and all of our extra packages, including Simmate. To make sure nothing ever breaks, it separates all of our installations into folders known as "environments". So using our example programs, we could have two enviornments: one named "simmate_env" and another named "old_program_env" (these can be named anything). The two different python versions and codes would be installed into separate folders -- so that they don't interact.

In reality, installing Simmate and other python packages is much more complicated than just needing two different python versions. We are going to Anaconda to manage all of this for us. Anaconda also installs programs that let's us write our own custom code too.


## Installing Anaconda and a first look

You don't need to make an account on their website. Just use their [their download page](https://www.anaconda.com/products/individual-d) and install their individual. Use all of the default options when installing and open up the application when you're done! The application will be called "Anaconda Navigator".

On the homescreen, you'll see a bunch of programs listed out for you, such as Orange3, Jupyter Notebook, Spyder, and others. These programs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, LibreOffice, and others for writing papers, all of these programs are different ways to write Python. Our prefered program is [Spyder](https://www.spyder-ide.org/), which we will walk through in tutorial 3.

<!-- This is an image of the Anaconda GUI home -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-defaults.png"  height=440 style="max-height: 440px;">
</p>

On the left of the screen, you'll see an "Enviornments" tab. Go ahaead and open it. When you first install Anaconda, there will only be a "base" environment that has a bunch of popular programs installed for you already. You can create new enviornments here and install new packages into each -- all without affecting what's already installed.

<!-- This is an image of the Anaconda GUI environments -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-env1.png"  height=440 style="max-height: 440px;">
</p>

That's really it to the Anaconda interface! While we can install Simmate with this interface, it's actually even easier with the command-line. We'll switch to that next.

If you want a more complete overview of Anaconda, they have a series of [getting-started guides](https://docs.anaconda.com/anaconda/user-guide/) available, but these guides aren't required for using Simmate (so don't spend any more than 10 minutes looking through them).

## Switching to the Command-line

While the interface is convenient if you've never written code before, it is much quicker (and easier!) to use the command-line. Don't worry, it's much simpler than most expect. Even if you don't know how to code, you can master the command-line in just a few minutes.

Each command can be viewed as a "button". For example, the command `cd` stands for "change directly". When you call it, it just opens up a new folder to view the contents -- so the same thing as double-clicking a folder to open it up!

Let's try this out with our command-line.

- On Windows 10, search for "Anaconda Powershell Prompt" in your apps (search bar in the bottom left of the screen) and open it up.
- On Macs and Linux, search for the app named "Terminal"

You should see something like this:

<!-- This is an image of an empty terminal with anaconda installed -->
<p align="center" style="margin-bottom:40px;">
<img src="https://aws1.discourse-cdn.com/codecademy/original/5X/0/4/8/7/0487a63480b3b9cd0fc056877d8abaa2b1e90e3d.png"  height=330 style="max-height: 330px;">
</p>

You'll see `(base)` at the start of the line. This is our anaconda enviornment that we are currently using. After that, you'll see the "current working directory", which is the folder we currently have open and are sitting in. On Windows this will be your user folder (e.g. `C:\Users\jacksund`) and for Mac/Linux you'll see `~` which is shorthand for your user folder (e.g. `home/jacksund`).

Now, try typing in the command `cd Desktop` and then hit enter. This will open up your Desktop folder. Then enter the command `ls`, which will list all files and folders on your Desktop. 

For other simple commands, you can take a look at [this cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) or take [a full tutorial](https://www.codecademy.com/learn/learn-the-command-line). Memorizing commands will come slowly over time, so keep this cheat-sheet handy. We highly recommend that you spend 30 minutes going through these links once you finish this tutorial.

Obviously, the tricky part with the command-line is knowing what to type. Typically, programs have a base command where you can start though. For anaconda, the command is `conda`. If you aren't sure what it does or how to use it, you just add `--help` to it. Type in the command `conda --help` and you'll see an output like this:

```
usage: conda [-h] [-V] command ...

conda is a tool for managing and deploying applications, environments and packages.

<< TO SAVE SPACE FOR THE TUTORIAL, WE REMOVED THE REST OF THE OUTPUT >>
```

Don't get overwhelmed by the amount of information printed out. Each line is getting accross a simple idea. 

For example, the line `-h, --help     Show this help message and exit.` is telling us what the `conda --help` command does! It also tells us that we could have done `conda -h` for the same output.

It also tells us there are other "subcommands" available. One is `create` which says it creates a new environment. To learn more about that one, we can run the command `conda create --help`. There's a bunch here... But again, you don't need to memorize all of this. Just remember how to get this help page when you need it. Up next, we'll use these commands to create our enviornment and install Simmate.

## Creating our environment and installing Simmate

For now, let's create a new environment that uses the [conda-forge](https://conda-forge.org/) channel. A channel is where anaconda downloads packages from -- and to keep things simple, we will ALWAYS use conda-forge (this is the standard in the python community). Now let's run this command below. Note you can switch out the name "my_env" for whatever you want here, just make sure you use underscores instead of spaces ("my_env" will work while "my env" will give an error).

```
conda install -c conda-forge -n my_env python=3.8
```

Say yes when the installation asks for confirmation. Next, we want switch to using this new environment. To do that we use...

```
conda activate my_env
```

You'll see the start of your command line switch from `(base)` to `(my_env)` if this worked successfully. Next, we want to install Simmate.

```
conda install -c conda-forge -n my_env simmate
```

This may take a few minutes to run and install. But once it's done, you've now successfully installed Simmate! If you ran into any errors with this very last command, please let our team know immediately by [posting a new issue here](https://github.com/jacksund/simmate/issues/new).

As an extra, let's use Anaconda to install [Sypder](https://www.spyder-ide.org/) too. Spyder is what we will use to write custom Python in later tutorials, so we'll talk more on this later. But now that we have Anaconda all set up, installing new programs can be done in just one line:
```
conda install -c conda-forge -n my_env spyder
```

## Exploring Simmate's command-line

Just like we were using `conda --help` above, we can also ask for help with Simmate's base command. Start with running the command `simmate --help` and you should see:

```
Usage: simmate [OPTIONS] COMMAND [ARGS]...

  This is the base command that all others stem from.

  If you are a beginner for the command line, take a look at our tutorial:
  << TODO: insert link >>

Options:
  --help  Show this message and exit.

Commands:
  database         A group of commands for managing your database.
  run-server       This runs a website test server locally for Simmate.
  start-project    This creates creates a new folder and fills it with an...
  workflow-engine  A group of commands for starting up Prefect Agents and...
  workflows        A group of commands for running workflows or viewing...
```

You can see there are many other commands like `simmate database` and `simmate workflows` that we will explore in other tutorials. 

But we're now ready to start using the code!

## Extra Resources
- [Anconda's getting-started guides](https://docs.anaconda.com/anaconda/user-guide/) (we recommend taking ~10min to glance through)
- [A command-line cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) (useful printout to have at your desk)
- [A full tutorial for the command-line](https://www.codecademy.com/learn/learn-the-command-line) (we HIGHLY recommended parts 1 and 2, which will take 1-2 hours)

*all tutorials that we recommend from codecademy.com can be completed before your free trial expires

