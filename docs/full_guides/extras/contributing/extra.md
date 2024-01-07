# Additional Guidelines and Suggestions

## Source Code Search
When you've made significant changes to a method, you might need to find all its instances in Simmate. You can use Spyder's `Find` window for this. Here's how to set it up:

1. In Spyder, go to the `View` tab (at the top of the window) > `Panes` > select `Find`.
2. The `Find` option should now appear in the top-right window of Spyder, alongside your `Help` window and `Variable Explorer`.
3. In the `Find` window, set `Exclude` to the following to prevent these files from being searched:
```
*.csv, *.dat, *.log, *.tmp, *.bak, *.orig, *.egg-info, *.svg, *.xml, OUTCAR, *.js, *.html
```
4. Set `Search in` to the `src/simmate` directory to limit the search to source code.

## Command-Line Git

While we suggest using [GitKraken](https://www.gitkraken.com/), there might be times when you need to use the git command-line. Github offers [detailed guides](https://docs.github.com/en/github/using-git/getting-started-with-git-and-github) for this, but we've summarized the essentials here.

To set up 2-factor-auth, follow these steps (according to [these instructions](https://docs.github.com/en/github/authenticating-to-github/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication)):

    1. Go to Profile >> Settings >> Account Security
    2. Click on "Enable two-factor" authentication
    3. Follow the prompts to finish setup (I used SMS and saved my codes to BitWarden)

To create your API token, follow these steps (according to [these instructions](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token)):

    1. Go to Profile >> Settings >> Developer Settings >> Personal Access tokens
    2. Generate a new token for 90 days with the "repo" scope and "read:org"
    3. Use this token as your password when running git commands

To set up permissions with git on the command-line, follow these steps (using [this guide](https://docs.github.com/en/get-started/getting-started-with-git/caching-your-github-credentials-in-git)):

    1. Make sure the GitHub CLI is installed (`conda install -c conda-forge gh`)
    2. Run `gh auth login` and follow the prompts to enter your personal token from above

Here are some frequently used commands...
``` bash
# To clone a remote directory to your local disk
git clone <GITHUB-URL>

# To pull a specific branch (main here) while in a git directory
git pull origin main

# To discard all changes and reset your branch
git restore .
```