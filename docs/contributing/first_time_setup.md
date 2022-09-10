
# First-time setup

!!! tip
    If you are a student or teacher, we recommend using your Github account with [Github's free Student/Teacher packages](https://education.github.com/). This includes Github Pro and many other softwares that you may find useful. This is optional.

1. Fork the Simmate repo to your Github profile (e.g. `yourname/simmate`)

2. Clone `yourname/simmate` to your local desktop. To do this, we recommend using [GitKraken](https://www.gitkraken.com/) and cloning to a folder named `~/Documents/github/`. Note, Gitkraken is free for public repos (which includes Simmate), but also available with [Github's free Student/Teacher packages](https://education.github.com/). Their [6 minute beginner video](https://www.youtube.com/watch?v=ub9GfRziCtU) will get you started.

3. Navigate to where you cloned the Simmate repo:
``` shell
cd ~/Documents/github/simmate
```

4. Create your conda env using our conda file. Note, this will install Spyder for you and name your new environment `simmate_dev`. We highly recommend you use Spyder as your IDE so that you have the same overall setup as the rest of the team.
``` shell
conda env update -f .github/environment.yaml
conda install -n simmate_dev -c conda-forge spyder -y
conda activate simmate_dev
```

5. Install Simmate in developmental mode to your `simmate_dev` env.
``` shell
pip install -e .
```

6. When resetting your database, make sure you do **NOT** use the prebuilt database. Pre-builts are only made for new releases and the dev database may differ from the most recent release.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
```

7. Make sure everything works properly by running our tests
``` shell
# you can optionally run tests in parallel 
# with a command such as "pytest -n 4"
pytest
```

8. In GitKraken, make sure you have the `main` branch of your repo (`yourname/simmate`) checked out.

9. In Spyder, go `Projects` > `New Project...`. Check `existing directory`, select your `~/Documents/github/simmate` directory, and then `create` your Project!

10. You can now explore the source code and add/edit files! Move to the next section on how to format, test, and submit these changes to our team.

