# Installing Anaconda

## Why Anaconda?

In an ideal world, you could download Simmate like any other desktop app and be ready to go. However, have you ever changed one thing on your computer only to find that another program stops working? This is a common occurrence with Python, so we need to tread carefully. For instance, consider the following scenario:

1. Simmate which requires Python version 3.10 or greater
2. A separate package which requires Python version 2.7

The conflicting Python versions pose a problem. To address this, we use [Anaconda](https://www.anaconda.com/). Anaconda installs Python and all our additional packages, including Simmate. To ensure nothing breaks, it isolates each of our installations into folders known as "environments".

Anaconda also prevents the installation of conflicting packages within a single environment.

!!! example
    With the two programs mentioned above, we could have two environments: one named `simmate_env` and another named `other_env` (you can name them anything). The two different Python versions and codes would be installed into separate folders to prevent interaction.

## Installing Anaconda and a first look

In this tutorial, we'll install Anaconda on your local desktop/laptop. Even if you plan to use a university supercomputer (or any other remote computer system) to run workflows, stick to your local computer for now. We'll transition to your remote supercomputer in a later tutorial.


### 1. Install Anaconda
To install Anaconda, you don't need to create an account on their website. Simply visit [their download page](https://www.anaconda.com/products/distribution) and install Anaconda. Stick to the default options during installation.


### 2. Open Anaconda
After the download is complete, launch the application, which will be named **Anaconda Navigator**.

On the home screen, you'll see several "IDEs", such as Orange3, Jupyter Notebook, Spyder, and others. These IDEs are for writing your own Python code. Just as there are multiple platforms like Microsoft Word, Google Docs, & LibreOffice for writing essays, these IDEs offer different ways to write Python. We recommend [Spyder](https://www.spyder-ide.org/), which we will introduce in a later tutorial.

<!-- This is an image of the Anaconda GUI home -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-tabs1.png"  height=440 style="max-height: 440px;">
</p>


### 3. View environments
On the left side of the application window, you'll find an **Environments** tab. Click on it. When you first install Anaconda, there will only be a `base`` environment with popular packages already installed. You can create new environments here and install new packages into each -- all without affecting what's already installed.

<!-- This is an image of the Anaconda GUI environments -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-env1.png"  height=440 style="max-height: 440px;">
</p>


### Final comments

That's all there is to the Anaconda interface! While we can install Simmate using this interface, it's actually simpler with the command-line. The rest of this tutorial will use the command-line instead of the Anaconda Navigator interface.

!!! tip
    If you want a more comprehensive overview of Anaconda, they offer a series of [getting-started guides](https://docs.anaconda.com/anaconda/user-guide/). However, these guides aren't necessary for using Simmate (so don't spend more than 10 minutes browsing through them).
