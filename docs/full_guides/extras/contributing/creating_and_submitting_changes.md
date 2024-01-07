# Changes Submission Guide

1. Prior to making any changes, please engage with our team to discuss your proposed alterations. This ensures everyone is informed about ongoing work and allows for constructive feedback. You can submit feature requests, bug reports, and other issues on our [Issues page](https://github.com/jacksund/simmate/issues). For general ideas and queries, please use our [Discussions page](https://github.com/jacksund/simmate/discussions).

2. [Ensure your fork is up-to-date](https://support.gitkraken.com/working-with-repositories/pushing-and-pulling/) with our main code at `jacksund/simmate`. This is essential if it's been a while since your last update. If you've just finished the previous section, you're good to go.

3. Access the Simmate directory in Spyder, as detailed in step 8 of the previous section.

4. Open the file you wish to edit in Spyder and make your changes.

5. Don't forget to save all file changes in Spyder.

6. Simmate demands clean, readable code. We utilize the [`black`](https://github.com/psf/black) formatter and [isort](https://pycqa.github.io/isort/docs/configuration/github_action.html) for managing imports. Execute these commands in the `~/Documents/github/simmate` directory:
``` shell
isort .
black .
```

7. Simmate employs [pytest](https://docs.pytest.org/en/6.2.x/) test cases to ensure new changes don't interfere with existing features. Run these tests to validate your changes. Execute this command in the `~/Documents/github/simmate` directory:
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

8. If all tests are successful, your changes are ready for submission to Simmate!

9. Use GitKraken to review your changes. If the changes are satisfactory, `stage` and `commit` them to the `main` branch of your repo (`yourname/simmate`). You can [add an emoji](https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md) to your commit message to show you've read the tutorial.

10. [Open a pull-request](https://support.gitkraken.com/working-with-repositories/pull-requests/) to merge your changes into our main code (`jacksund/simmate`). We'll review your changes and merge them if they meet our standards.

!!! tip
    You can also format files while coding with Spyder. Go to `Tools` -> `Preferences` -> `Completion and Linting` -> `Code Style and Formatting` > select `black` from the code formatting dropdown. To format an open file in Spyder, use the `Ctrl+Shift+I` shortcut.

!!! note
    Currently, Spyder does not have a plugin for pytest. We're eagerly awaiting the development of this feature along with their [Unittest plugin](https://www.spyder-ide.org/blog/introducing-unittest-plugin/).