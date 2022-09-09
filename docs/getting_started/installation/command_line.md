
# Switching to the Command-line

While the Anaconda Navigator interface is convenient if you've never written code before, it is much quicker (and easier!) to use the command-line. Don't worry, it's much simpler than you probably expect. Even if you don't know how to code, you can master the command-line in just a few minutes.

Each command can be viewed as a "button". For example, the command `cd` stands for "change directory". When you call it, it just opens up a new folder to view the contents -- so the same thing as double-clicking a folder to open it up.

----------------------------------------------------------------------

## Running our first command

Let's try this out with our command-line.

- On Windows, search for and open "Anaconda Powershell Prompt" using your Start menu.
- On Mac and Linux, search for and open the app named "Terminal"

You should see something like this:

<!-- This is an image of an empty terminal with anaconda installed -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.shaileshjha.com/wp-content/uploads/2020/03/anaconda_powershell_prompt-800x450.jpg"  height=330 style="max-height: 330px;">
</p>

You'll see `(base)` at the start of the line. This is our anaconda enviornment that we are currently using. After that, you'll see the "current working directory", which is the folder we currently have open and are sitting in. On Windows this will be your user folder (e.g. `C:\Users\jacksund`) and for Mac/Linux you'll see `~` which is shorthand for your user folder (e.g. `home/jacksund`).

Now, try typing in the command `cd Desktop` and then hit enter. This will open up your Desktop folder. Then enter the command `ls`, which will list all files and folders on your Desktop. 

``` shell
# run these two commands
cd Desktop
ls
```

----------------------------------------------------------------------

## Learning new commands

!!! tip 
    For other simple commands, you can take a look at [this cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) or take [a full tutorial](https://www.codecademy.com/learn/learn-the-command-line). Memorizing commands will come slowly over time, so keep this cheat-sheet handy. We highly recommend that you spend 30 minutes going through these links once you finish this tutorial.

Obviously, the tricky part with the command-line is knowing what to type. Fortunately, however, most programs have a single command that forms the base of more complex commands. For anaconda, the command is `conda`. If you aren't sure what it does or how to use it, you just add `--help` to it. Type in the command `conda --help` and you'll see an output like this:

``` shell
conda --help
```

``` shell
usage: conda [-h] [-V] command ...

conda is a tool for managing and deploying applications, environments and packages.

Options:

positional arguments:
  command
    clean        Remove unused packages and caches.
    compare      Compare packages between conda environments.
    config       Modify configuration values in .condarc. This is modeled after the git config command. Writes to the user .condarc file (/home/jacksund/.condarc) by default.
    create       Create a new conda environment from a list of specified packages.
    info         Display information about current conda install.
    init         Initialize conda for shell interaction. [Experimental]
    install      Installs a list of packages into a specified conda environment.
    list         List linked packages in a conda environment.
    package      Low-level conda package utility. (EXPERIMENTAL)
    remove       Remove a list of packages from a specified conda environment.
    uninstall    Alias for conda remove.
    run          Run an executable in a conda environment.
    search       Search for packages and display associated information. The input is a MatchSpec, a query language for conda packages. See examples below.
    update       Updates conda packages to the latest compatible version.
    upgrade      Alias for conda update.

optional arguments:
  -h, --help     Show this help message and exit.
  -V, --version  Show the conda version number and exit.

conda commands available from other packages:
  build
  content-trust
  convert
  debug
  develop
  env
  index
  inspect
  metapackage
  pack
  render
  repo
  server
  skeleton
  token
  verify

```

Don't get overwhelmed by the amount of information printed out. Each line is getting accross a simple idea. 

For example, the line `-h, --help     Show this help message and exit.` is telling us what the `conda --help` command does! It also tells us that we could have done `conda -h` for the same output.

This help message also tells us there are other "subcommands" available. One is `create` which says it creates a new environment. To learn more about that one, we can run the command `conda create --help`. 

There's a bunch here... But again, you don't need to memorize all of this. Just remember how to get this help page when you need it. Up next, we'll use these commands to create our environment and install Simmate.

----------------------------------------------------------------------
