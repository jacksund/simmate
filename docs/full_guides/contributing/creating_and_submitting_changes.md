# Changes Submission Guide

1. Prior to making any changes, please inform our team to discuss your proposed updates using a github issue. This ensures everyone is informed about ongoing work and allows for constructive feedback. You can submit feature requests, bug reports, and other issues on our [Issues page](https://github.com/jacksund/simmate/issues). For general ideas and queries, please use our [Discussions page](https://github.com/jacksund/simmate/discussions).

2. [Ensure your fork is up-to-date](https://support.gitkraken.com/working-with-repositories/pushing-and-pulling/) with our main code at `jacksund/simmate`. This is essential if it's been a while since your last update.

3. Open the file you wish to edit in your IDE and make your changes.

4. Don't forget to save all file changes.

5. Simmate enforces clean, readable code. We utilize the [`black`](https://github.com/psf/black) formatter, [isort](https://pycqa.github.io/isort/docs/configuration/github_action.html) for managing imports, and [djlint](https://github.com/djlint/djLint) for formatting html templates:
``` shell
isort .
black .
djlint . --reformat
```

6. Simmate uses [pytest](https://docs.pytest.org/en/6.2.x/) (+ plugins) to ensure new changes don't interfere with existing features. Run these tests to validate your changes:
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

7. If all tests are successful, your changes are ready for submission to Simmate!

8. Use GitKraken to review your changes. If the changes are satisfactory, `stage` and `commit` them to the new branch of your repo (`yourname/simmate`).

9.  [Open a pull-request](https://support.gitkraken.com/working-with-repositories/pull-requests/) to merge your changes into our main code (`jacksund/simmate`), and we will review your changes! For fun, you can [add an emoji](https://github.com/ikatyang/emoji-cheat-sheet/blob/master/README.md) to your pull request title to show you've read the tutorial.
