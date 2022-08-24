
# Creating and submitting changes

1. Make sure you have contacted our team on the changes you wish to make. This lets everyone know what is being working on and allows other contributors to give feedback/advice. You can request features, report bugs, etc. in our [Issues page](https://github.com/jacksund/simmate/issues). General ideas and questions are better suited for our [Discussions page](https://github.com/jacksund/simmate/discussions).

2. [Make sure your fork is up to date](https://support.gitkraken.com/working-with-repositories/pushing-and-pulling/) with our main code at `jacksund/simmate`. This is only important if it's been more than a couple days since your last update. So if you just completed the previous section, you should be good to go here.

3. Have the Simmate directory open in Spyder. This was done in steo 8 of the previous section.

4. In Spyder, open the file you want and make your edits! :fire::fire::rocket:

5. Make sure you saved all file changes in Spyder.

6. Simmate requires code to be nicely formatted and readable. To do this, we use the [`black`](https://github.com/psf/black) formatter and [isort](https://pycqa.github.io/isort/docs/configuration/github_action.html) for organzing imports. Make sure you are in the `~/Documents/github/simmate` directory when you run these two commands:
``` shell
isort .
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
