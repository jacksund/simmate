
# Contributing to Simmate

In this guide, you will learn how to contribute new features to Simmate's code.

1. [Learning about core dependencies](#learning-about-core-dependencies)
2. [First-time Setup](#first-time-setup)
3. [The full tutorial](#the-full-tutorial)

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

4. Create your conda env using our conda file. Note, this will install Spyder for you and name your new environment `simmate_dev`.
``` shell
conda env update -f tutorials/Guides_for_contributors/environment.yaml
conda activate simmate_dev
```

5. Install Simmate in developmental mode to your `simmate_dev` env.
``` shell
pip install -e .
```

6. Make sure everything works properly by running our tests
``` shell
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
pytest
```

> :warning: Spyder does not yet have a plugin for pytest. We are still waiting on this feature to be built alongside their [Unittest plugin](https://www.spyder-ide.org/blog/introducing-unittest-plugin/).

8. If everything passes, your changes can be accepted into Simmate! :partying_face:

9. Open GitKraken, and you should then see your changes listed. For changes that you are happy with, `stage` and then `commit` them to the `main` branch of your repo (`yourname/simmate`). Feel free to [add an emoji](https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md) to the start of your commit message. These icons simply tell us that you read the tutorial (and also emojis are a fun distraction).

10. Now [open a pull-request](https://support.gitkraken.com/working-with-repositories/pull-requests/) to merge your changes into our main code (currently at `jacksund/simmate`). We will review your changes and merge them if they pass all of our checks.
