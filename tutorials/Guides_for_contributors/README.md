
# Contributing to Simmate

In this guide, you will learn how to contribute new features to Simmate's code.

1. [Learning about core dependencies](#learning-about-core-dependencies)
2. [First-time Setup](#first-time-setup)
3. [Creating and submitting changes](#creating-and-submitting-changes)
4. [Extra notes and tips](#extra-notes-and-tips)
5. [For maintainers](#for-maintainers)

<br/><br/>

# Learning about core dependencies

When you first join our community, you may only be comfortable fixing typos and adding small utilities/functions. But if you would like to make larger changes/contribution to Simmate, we highly recommend learning about our core dependencies. This includes...

- [Django](https://docs.djangoproject.com/en/4.0/) for our database and website
- [Prefect](https://docs.prefect.io/core/) for our workflows and scheduler
- [Dask](https://docs.dask.org/en/stable/futures.html) for clusters and execution


<br/><br/>

# First-time setup

> :bulb: If you are a student or teacher, we recommend using your Github account with [Github's free Student/Teacher packages](https://education.github.com/). This includes Github Pro and many other softwares that you may find useful. This is optional.

1. Fork the Simmate repo to your Github profile (e.g. `yourname/simmate`)

2. Clone `yourname/simmate` to your local desktop. To do this, we recommend using [GitKraken](https://www.gitkraken.com/) and cloning to a folder named `~/Documents/github/`. Note, Gitkraken is free for public repos (which includes Simmate), but also available with [Github's free Student/Teacher packages](https://education.github.com/). Their [6 minute beginner video](https://www.youtube.com/watch?v=ub9GfRziCtU) will get you started.

3. Navigate to where you cloned the Simmate repo:
``` shell
cd ~/Documents/github/simmate
```

4. Create your conda env using our conda file. Note, this will install Spyder for you and name your new environment `simmate_dev`. We highly recommend you use Spyder as your IDE so that you have the same overall setup as the rest of the team.
``` shell
conda env update -f tutorials/Guides_for_contributors/environment.yaml
conda install -n simmate_dev -c conda-forge spyder -y
conda activate simmate_dev
```

5. Install Simmate in developmental mode to your `simmate_dev` env.
``` shell
pip install -e .
```

6. Make sure everything works properly by running our tests
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

7. In GitKraken, make sure you have the `main` branch of your repo (`yourname/simmate`) checked out.

8. In Spyder, go `Projects` > `New Project...`. Check `existing directory`, select your `~/Documents/github/simmate` directory, and then `create` your Project!

9. You can now explore the source code and add/edit files! Move to the next section on how to format, test, and submit these changes to our team.

<br/><br/>

# Creating and submitting changes

1. Make sure you have contacted our team on the changes you wish to make. This lets everyone know what is being working on and allows other contributors to give feedback/advice. You can request features, report bugs, etc. in our [Issues page](https://github.com/jacksund/simmate/issues). General ideas and questions are better suited for our [Discussions page](https://github.com/jacksund/simmate/discussions).

2. [Make sure your fork is up to date](https://support.gitkraken.com/working-with-repositories/pushing-and-pulling/) with our main code at `jacksund/simmate`. This is only important if it's been more than a couple days since your last update. So if you just completed the previous section, you should be good to go here.

3. Have the Simmate directory open in Spyder. This was done in steo 8 of the previous section.

4. In Spyder, open the file you want and make your edits! :fire::fire::rocket:

5. Make sure you saved all file changes in Spyder.

6. Simmate requires code to be nicely formatted and readable. To do this, we use the [`black`](https://github.com/psf/black) formatter. Make sure you are in the `~/Documents/github/simmate` directory when you run this command:
``` shell
black .
```

> :bulb: you can optionally format files as you code with Spyder too. `Tools` -> `Preferences` -> `Completion and Linting` -> `Code Style and Formatting` > Under code formatting dropdown, select `black`. To format a file you have open in Spyder, use the the `Ctrl+Shift+I` shortcut.

7. Simmate has test cases to make sure new changes don't break any of Simmate's existing features. These are written using [pytest](https://docs.pytest.org/en/6.2.x/). Run these to check your changes. Make sure you are in the `~/Documents/github/simmate` directory when you run this command:
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

> :warning: Spyder does not yet have a plugin for pytest. We are still waiting on this feature to be built alongside their [Unittest plugin](https://www.spyder-ide.org/blog/introducing-unittest-plugin/).

8. If everything passes, your changes can be accepted into Simmate! :partying_face:

9. Open GitKraken, and you should then see your changes listed. For changes that you are happy with, `stage` and then `commit` them to the `main` branch of your repo (`yourname/simmate`). Feel free to [add an emoji](https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md) to the start of your commit message. These icons simply tell us that you read the tutorial (and also emojis are a fun distraction).

10. Now [open a pull-request](https://support.gitkraken.com/working-with-repositories/pull-requests/) to merge your changes into our main code (currently at `jacksund/simmate`). We will review your changes and merge them if they pass all of our checks.

<br/><br/>

# Extra notes and tips

### Searching the source code
If you changed a method significantly, you may need to find all places in Simmate that it is used. You can easily search for these using Spyders `Find` window. Use these steps to set up this window:

1. In Spyder, go to the `View` tab (top of window) > `Panes` > check `Find`
2. In the top-right window of spyder, you should now see the `Find` option. This will share a window with your `Help` window and `Variable Explorer`
3. In the `Find` window, set `Exclude` to the following: (we don't want to search these files)
```
*.csv, *.dat, *.log, *.tmp, *.bak, *.orig, *.egg-info, *.svg, *.xml, OUTCAR, *.js, *.html
```
4. Set `Search in` to the `src/simmate` directory so that you only search source code.


### Git in the command-line

While we recommand sticking with [GitKraken](https://www.gitkraken.com/), you may need to use the git command-line in some scenarios. Github has [extensive guides](https://docs.github.com/en/github/using-git/getting-started-with-git-and-github) on how to do this, but we outline the basics here.

For configuring 2-factor-auth, we follow directions from [here](https://docs.github.com/en/github/authenticating-to-github/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication). To summarize:

    1. Go to Profile >> Settings >> Account Security
    2. Select "Enable two-factor" authentication
    3. Follow the prompt to set up (I used SMS and save my codes to BitWarden)

For configuring your API token, we follow directions from [here](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token). To summarize:

    1. Go to Profile >> Settings >> Developer Settings >> Personal Access tokens
    2. Generate new token for 90 days and with the "repo" scope and "read:org"
    3. You now use this token as your password when running git commands

And to configure permissions with git on the command-line (using [this guide](https://docs.github.com/en/get-started/getting-started-with-git/caching-your-github-credentials-in-git)):

    1. make sure github cli is installed (`conda install -c conda-forge gh`)
    2. run `gh auth login` and follow prompts to paste in personal token from above


Lastly, some common commands include...
``` bash
# to copy a remote directory to your local disk
git clone <GITHUB-URL>

# while in a git directory, this pulls a specific branch (main here)
git pull origin main

# To remove all changes and reset your branch
git restore .
```

<br/><br/>

# For maintainers

(currently this section is only relevant to @jacksund)

To make a new release, you must follow these steps:

1. Create the new documentation:
``` bash
# Before the new documentation can be produced, there are a number
# of optional dependencies that need to be installed.
conda install -n simmate_dev -c conda-forge jarvis-tools aflow -y
pip install qmpy_rester

# You can the change into the docs directory and run the make_docs.py.
# Note we also delete existing docs to ensure a clean setup.
cd docs/
rm -r simmate/ index.html search.js simmate.html
python make_docs.py
```

2. Update the Simmate version number in `setup.py` ([here](https://github.com/jacksund/simmate/blob/main/setup.py))

3. Make a [release](https://github.com/jacksund/simmate/releases/new) on Github (which will automatically release to pypi)

4. Wait for the autotick bot to open a pull request for the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). This can take up to 24hrs, but you can check the status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

5. Make sure the autotick bot made the proper changes before merging. If there were any major changes, you can use [grayskull](https://www.marcelotrevisani.com/grayskull) to help update the version number, sha256, and dependencies.

6. After merging, it takes the conda-forge channels 30min or so to update their indexes. Afterwards, you can test the conda install with:
``` bash
# for a normal release
conda create -n my_env -c conda-forge simmate -y

# for a dev release
conda create -n my_env -c conda-forge python=3.10 -y
conda install -n my_env -c conda-forge -c conda-forge/label/simmate_dev simmate -y

# as an extra, make sure spyder can also be installed in the same env
conda install -n my_env -c conda-forge spyder -y
```
