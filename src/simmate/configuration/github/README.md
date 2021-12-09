
# NOTES ON GIT

For easiest use, stick with [Github Desktop](https://desktop.github.com/)

For the command-line (linux):
    git clone <GITHUB-URL>
    git pull origin main
    git config --global credential.helper cache
Read more at
    https://docs.github.com/en/github/using-git/getting-started-with-git-and-github

# Configuring tokens

Following directions from...
https://docs.github.com/en/github/authenticating-to-github/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication

1. Go to Profile >> Settings >> Account Security
2. Select "Enable two-factor" authentication
3. Follow the prompt to set up (I used SMS and save my codes to BitWarden)

Following directions from...
https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token

1. Go to Profile >> Settings >> Developer Settings >> Personal Access tokens
2. Generate new token for 90 days and with the "repo" scope and "read:org"
3. You now use this token as your password when running git commands

And to configure permissions with git on the command-line:
https://docs.github.com/en/get-started/getting-started-with-git/caching-your-github-credentials-in-git

1. make sure github cli is installed (`conda install -c conda-forge gh`)
2. run `gh auth login` and follow prompts to paste in personal token from above

To remove all changes...
    git restore .
