
# Switching to the Command-line

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
