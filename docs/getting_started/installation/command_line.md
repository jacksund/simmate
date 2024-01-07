# Transitioning to the Command-line

While the Anaconda Navigator interface is user-friendly for beginners, using the command-line is faster and more efficient. Don't fret, it's simpler than it seems. Even if you're not familiar with coding, you can learn the command-line basics in a few minutes.

Think of each command as a "button". For instance, the command `cd` stands for "change directory". When you use it, it opens a new folder to view its contents -- similar to double-clicking a folder to open it.

----------------------------------------------------------------------

## Executing our first command

Let's get started with our command-line.

- On Windows, search for and open "Anaconda Powershell Prompt" using your Start menu.
- On Mac and Linux, search for and open the app named "Terminal"

You should see something like this:

<!-- This is an image of an empty terminal with anaconda installed -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.shaileshjha.com/wp-content/uploads/2020/03/anaconda_powershell_prompt-800x450.jpg"  height=330 style="max-height: 330px;">
</p>

You'll notice `(base)` at the start of the line. This represents our current anaconda environment. Following that, you'll see the "current working directory", which is the folder we currently have open. On Windows, this will be your user folder (e.g. `C:\Users\jacksund`) and for Mac/Linux, you'll see `~` which is shorthand for your user folder (e.g. `home/jacksund`).

Now, type in the command `cd Desktop` and press enter. This will open your Desktop folder. Then enter the command `ls`, which will list all files and folders on your Desktop. 

``` shell
# run these two commands
cd Desktop
ls
```

----------------------------------------------------------------------

## Mastering new commands

!!! tip 
    For more basic commands, refer to [this cheat sheet](https://www.git-tower.com/blog/command-line-cheat-sheet/) or take [a comprehensive tutorial](https://www.codecademy.com/learn/learn-the-command-line). Remembering commands will come gradually, so keep this cheat-sheet handy. We strongly suggest that you spend 30 minutes going through these links after completing this tutorial.

The challenging part with the command-line is knowing what to type. However, most programs have a single command that forms the base of more complex commands. For anaconda, the command is `conda`. If you're unsure about its function or usage, simply add `--help` to it. Type in the command `conda --help` and you'll see an output like this:

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

Don't be daunted by the volume of information displayed. Each line conveys a simple concept. 

For instance, the line `-h, --help     Show this help message and exit.` explains what the `conda --help` command does! It also indicates that we could have used `conda -h` for the same output.

This help message also reveals other "subcommands" available. One is `create` which creates a new environment. To learn more about that, we can run the command `conda create --help`. 

There's a lot here... But remember, you don't need to memorize all of this. Just remember how to access this help page when you need it. Next, we'll use these commands to create our environment and install Simmate.

----------------------------------------------------------------------