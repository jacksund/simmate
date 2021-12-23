# Installing Simmate while Learning the Command-line

1. [The quick tutorial](#the-quick-version)
2. [The full tutorial](#the-full-tutorial)
    - [Why Anaconda?](#why-anaconda)
    - [Installing Anaconda and a first look](#installing-anaconda-and-a-first look)
    - [Switching to the Command-line](#switching-to-the-command-line)
    - [Creating our environment and installing Simmate](#creating-our-environment-and-installing-simmate)
    - [Exploring Simmate's command-line](#exploring-simmates-command-line)

# The quick version

1. Install [anaconda](https://www.anaconda.com/products/individual-d)
2. Create a conda enviornment, install Simmate in it, and activate it. *(note: Spyder is optional but recommended)*
```
conda create -n my_env -c conda-forge python=3.8 simmate spyder
conda activate my_env
```
3. Run the `simmate` command to make sure it's installed correctly

# The full tutorial

## Why Anaconda?

Ideally, you could download Simmate like any desktop app and then you'd be good to go. However, Simmate and the many other toolkits written in Python need to be carefully installed and configured. Have you ever installed a new program and then everything else on your computer goes haywire? With python, the chances of that happening are extremely high, so we want to be careful. Installing in this way also let's us write our own custom code!

To take care of this, we use [Anaconda](https://www.anaconda.com/products/individual-d). Anaconda takes care of installing Python and all of our extra packages, including Simmate. For example, say I wanted two programs installed:

1. Simmate which requires Python 3.8 or greater
2. Some very old program that requires Python 2.6

We normally wouldn't be able to have both at the same time because of the conflicting python versions, but with Anaconda, we can! To make sure nothing ever breaks, it separates all of our installations into folders known as "environments". Here, we could have enviornments named "simmate_env" and "old_program_env" (these can be named anything), were all the relevent programs are installed in separate folders -- so that they don't interact.

## Installing Anaconda and a first look

You don't need to make an account or anything on their website. Just download their individual version to your desktop from [their download page](https://www.anaconda.com/products/individual-d). Use all of the default options and open up the application when you're done!

On the homescreen, you'll see a bunch of programs listed out for you, such as Orange3, Jupyter Notebook, Spyder, and others. These programs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, LibreOffice, and others for writing papers, all of these programs are different ways to write Python. Our prefered program is [Spyder](https://www.spyder-ide.org/), which we will walk through in tutorial number 3.

<!-- This is an image of the Anaconda GUI home -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-defaults.png"  height=440 style="max-height: 440px;">
</p>

On the left of the screen, you'll see an "Enviornments" tab. Let's open it. When you first install anaconda, there will only be a "base" environment that has a bunch of popular programs installed for you already. You can create new enviornments here and install new packages without affect anything that's already installed.

<!-- This is an image of the Anaconda GUI environments -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-env1.png"  height=440 style="max-height: 440px;">
</p>

That's really it to the Anaconda interface! For more help, take a look at [their guides and documentation](https://docs.anaconda.com/anaconda/).

## Switching to the Command-line

While the interface is super nice for those new to coding, you'll need to become confortable with the command-line. Don't worry, it's much simpler than most expect. You don't need to know how to code at all.

Each command can be viewed as a "button". For example, the command `cd` stands for "change directly". When you call it, it just opens up a new folder to view the contents -- so the same thing as double-clicking a folder to open it up!

Let's try this out with our command-line.

- On Windows 10, search for "Anaconda Powershell Prompt" in your apps (search bar in the bottom left of the screen) and open it up.
- On Macs and Linux, search for the app named "Terminal"

You should see something like this:

<!-- This is an image of an empty terminal with anaconda installed -->
<p align="center" style="margin-bottom:40px;">
<img src="https://aws1.discourse-cdn.com/codecademy/original/5X/0/4/8/7/0487a63480b3b9cd0fc056877d8abaa2b1e90e3d.png"  height=330 style="max-height: 330px;">
</p>

You'll see `(base)` at the start of the line. This is our anaconda enviornment that we are currently using. The line will then list off the "current working directory", where working directory is just the folder we currently have open and are sitting in. On Windows this will be your user folder like `C:\Users\jacksund` and for Mac/Linux you'll see `~` which is just shorthand for your user folder like `home/jacksund`.

Now, try typing in the command `cd Desktop` and then hit enter. This will open up your Desktop folder. Then try the command `ls`, which will list all files and folders on your Desktop. 

For other simple commands, you can take a look at [this cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) or take [a full tutorial](https://www.codecademy.com/learn/learn-the-command-line). Learning other commands will come slowly over time, and we'll tell you

Obviously, the tricky part with the command-line is knowing what to type. Typically, programs have a base command where you can start though. For anaconda, the command is `conda`. If you aren't sure what it does or how to use it, you just add `--help` to it. Type in the command `conda --help` and you'll see an output like this:

```
usage: conda [-h] [-V] command ...

conda is a tool for managing and deploying applications, environments and packages.

<< TO SAVE SPACE FOR THE TUTORIAL, WE REMOVED THE REST OF THE OUTPUT >>
```

Don't get overwhelmed by the amount of information printed out. Each line is getting accross a simple idea. 

For example, the line `-h, --help     Show this help message and exit.` is telling us what the `conda --help` command does! It also tells us that we could have done `conda -h` instead for the same thing.

It also tells us there are other "subcommands" available. One is `create` which says it creates a new environment! To learn more about that one, we can run the command `conda create --help`. There's a bunch here... But again, you don't need to learn any of this yet. It will come slowly over time. Up next, we'll use these commands to create our enviornment and install Simmate.

## Creating our environment and installing Simmate

For now, let's create a new environment that uses the [conda-forge](https://conda-forge.org/) channel (a channel is where anaconda downloads packages from -- and conda-forge is the one nearly all codes upload their packages to). Note you can switch out the name "my_env" for whatever you want here, just make sure you use underscores instead of spaces ("my_env" will work while "my env" will give an error).

```
conda install -c conda-forge -n my_env python=3.8
```

Say yes when the installation asks for confirmation. Next, we want switch to using this new environment. To do that we use...

```
conda activate my_env
```

You'll see the start of your command line switch from `(base)` to `(my_env)` if this worked successfully. Next, we want to install Simmate and Spyder. Spyder is what we will use to write custom Python in later tutorials, so we'll talk more on this later.

```
conda install -c conda-forge -n my_env simmate spyder
```

This may take a few minutes to run and install. But once it's done, you've now successfully installed Simmate! If you ran into any errors with this very last command, please let our team know immediately by [posting a new issue here](https://github.com/jacksund/simmate/issues/new).


## Exploring Simmate's command-line

Just like we were using `conda --help` above, we also ask for help with Simmate's base command, which is just `simmate`. Start with trying the command `simmate --help` and you should see:

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
