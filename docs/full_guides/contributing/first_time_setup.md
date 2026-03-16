# Getting Started

!!! tip
    We recommend students and teachers to use their Github accounts with [Github's free Student/Teacher packages](https://education.github.com/). This includes Github Pro and other beneficial software. However, this is not mandatory.

1. Fork the Simmate repository to your Github profile (e.g., `yourname/simmate`). The button to fork is at the top right of [Simmate's home github page](https://github.com/jacksund/simmate), near the "star repo" button.

2. Clone `yourname/simmate` to your local desktop. We recommend using [GitKraken](https://www.gitkraken.com/) and cloning to a folder named `~/Documents/git/`. GitKraken is free for public repositories (including Simmate), but is also part of [Github's free Student/Teacher packages](https://education.github.com/). Their [6-minute beginner video](https://www.youtube.com/watch?v=ub9GfRziCtU) provides a quickstart guide.

3. Navigate to the cloned Simmate repository:
``` shell
cd ~/Documents/git/simmate
```

4. Install [uv](https://docs.astral.sh/uv/) and use it to create your virtual environment and install all dependencies:
``` shell
uv sync --all-extras
```

5. Activate your new virtual environment. 
``` shell
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

6. It is best practice to have an fresh, empty database when developing:
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
```

7. Confirm everything is functioning correctly by running our tests
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

8. In GitKraken, you will start with `main` branch of your repository (`yourname/simmate`) checked out. Create a new branch and name it according to the changes you will make (e.g. `my-new-feature`).

9. Open the `simmate` folder in your preferred IDE (we recommend [Spyder](https://www.spyder-ide.org/) or [VS Code](https://code.visualstudio.com/)). Ensure your IDE is using the Python interpreter from the `.venv` folder you just created.

10.  You're now set to explore the source code and modify or add files! Continue to the next section for guidance on formatting, testing, and submitting your changes to our team.
