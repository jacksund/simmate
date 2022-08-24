
# Extra notes and tips

## Searching the source code
If you changed a method significantly, you may need to find all places in Simmate that it is used. You can easily search for these using Spyders `Find` window. Use these steps to set up this window:

1. In Spyder, go to the `View` tab (top of window) > `Panes` > check `Find`
2. In the top-right window of spyder, you should now see the `Find` option. This will share a window with your `Help` window and `Variable Explorer`
3. In the `Find` window, set `Exclude` to the following: (we don't want to search these files)
```
*.csv, *.dat, *.log, *.tmp, *.bak, *.orig, *.egg-info, *.svg, *.xml, OUTCAR, *.js, *.html
```
4. Set `Search in` to the `src/simmate` directory so that you only search source code.


## Git in the command-line

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
