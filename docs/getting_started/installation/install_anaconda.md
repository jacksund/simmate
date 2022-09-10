# Installing Anaconda

## Why Anaconda?

Ideally, you could download Simmate like any desktop app and then be good to go. But have you ever updated your operating system and then everything else on your computer goes haywire? With python, the chances of that happening are extremely high, so we want to be careful. For example, say I wanted two packages installed:

1. Simmate version 1.0, which requires python version 3.10 or greater
2. NumPy version 1.15, which requires python version 2.7

The conflicting versions of python creates a problem. To solve this, we use [Anaconda](https://www.anaconda.com/). Anaconda installs python and all of our extra packages, including Simmate. To make sure nothing ever breaks, it separates each of our installations into folders known as "environments". 

Package versions can also conflict with each other. Therefore, Anaconda also prevents you from installing conflicting versions within a single environment.

!!! example
    Using the 2 programs given above, we could have two environments: one named `simmate_env` and another named `numpy_env` (these can be named anything). The two different python versions and codes would be installed into separate folders so that they don't interact.

!!! example
    Simmate requires the package Django (version >3.2), so if you installed Django 2.0, it would break your Simmate installation. Anaconda will catch your mistake before it causes confusing errors elsewhere.


## Installing Anaconda and a first look

For this tutorial, we'll install Anaconda to your local desktop/laptop. Even if you'll be using a university supercomputer (or some other remote computer system) to run workflows, stick to your local computer. We'll switch to your remote supercomputer in a later tutorial.


### 1. Install Anaconda
To install Anaconda, you don't need to make an account on their website. Just use [their download page](https://www.anaconda.com/products/distribution) and install Anaconda. Use all of the default options when installing.


### 2. Open Anaconda
Once the download is finished, open up the application. The application will be called **Anaconda Navigator**.

On the homescreen, you'll see several IDEs, such as Orange3, Jupyter Notebook, Spyder, and others. These IDEs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, LibreOffice, and others for writing papers, all of these IDEs are different ways to write python. Our prefered IDE is [Spyder](https://www.spyder-ide.org/), which we will introduce in a later tutorial.

<!-- This is an image of the Anaconda GUI home -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-home.png"  height=440 style="max-height: 440px;">
</p>


### 3. View environments
On the left side of the application window, you'll see an **Environments** tab. Go ahead and open it. When you first install Anaconda, there will only be a "base" environment that already has popular packages installed. You can create new environments here and install new packages into each -- all without affecting what's already installed.

<!-- This is an image of the Anaconda GUI environments -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.anaconda.com/_images/nav-env1.png"  height=440 style="max-height: 440px;">
</p>


### Final comments

That's really it to the Anaconda interface! While we can install Simmate with this interface, it's actually even easier with the command-line. The remainder of this tutorial will use the command-line instead of the Anaconda Navigator interface.

!!! tip
    If you want a more complete overview of Anaconda, they have a series of [getting-started guides](https://docs.anaconda.com/anaconda/user-guide/) available, but these guides aren't required for using Simmate (so don't spend any more than 10 minutes looking through them).
