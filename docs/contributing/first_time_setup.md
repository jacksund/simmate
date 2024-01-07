# Getting Started

!!! tip
    We recommend students and teachers to use their Github accounts with [Github's free Student/Teacher packages](https://education.github.com/). This includes Github Pro and other beneficial software. However, this step is not mandatory.

1. Fork the Simmate repository to your Github profile (e.g., `yourname/simmate`).

2. Clone `yourname/simmate` to your local desktop. We recommend using [GitKraken](https://www.gitkraken.com/) and cloning to a folder named `~/Documents/github/`. GitKraken is free for public repositories (including Simmate), but is also part of [Github's free Student/Teacher packages](https://education.github.com/). Their [6-minute beginner video](https://www.youtube.com/watch?v=ub9GfRziCtU) provides a quick start guide.

3. Navigate to the cloned Simmate repository:
``` shell
cd ~/Documents/github/simmate
```

4. Create your conda environment using our conda file. This will install Spyder and name your new environment `simmate_dev`. We highly recommend using Spyder as your IDE for consistency with the rest of the team.
``` shell
conda env update -f envs/conda/dev.yaml
conda install -n simmate_dev -c conda-forge spyder -y
conda activate simmate_dev
```

5. Install Simmate in development mode to your `simmate_dev` environment.
``` shell
pip install -e .
```

6. When resetting your database, refrain from using the prebuilt database. Pre-builts are only created for new releases, and the development database may differ from the latest release.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
```

7. Confirm everything is functioning correctly by running our tests
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

8. In GitKraken, make sure you have the `main` branch of your repository (`yourname/simmate`) checked out.

9. In Spyder, navigate to `Projects` > `New Project...`. Select `existing directory`, choose your `~/Documents/github/simmate` directory, and then `create` your Project!

10. You're now set to explore the source code and modify or add files! Continue to the next section for guidance on formatting, testing, and submitting your changes to our team.