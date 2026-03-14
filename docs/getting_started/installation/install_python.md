# Choosing an Environment Manager

Before installing Simmate, you need a tool to manage your Python "environments." This ensures that Simmate and its dependencies don't interfere with other software on your computer.

---

## Which tool should I use?

We recommend choosing based on your comfort level with coding:

### Option 1: uv (Recommended)

**Best for:** Most users, including those comfortable with (or willing to learn) the command line.

- **Speed:** Extremely fast. What takes Anaconda 10 minutes to "solve," uv can often do in seconds.
- **Simplicity:** A single, lightweight tool that handles everything.
- **Installation:** Continue with the instructions below.

### Option 2: Anaconda

**Best for:** Absolute beginners who prefer a graphical interface (buttons and menus) to get started.

- **Ease of Use:** Includes **Anaconda Navigator**, a visual dashboard for managing your software.
- **Trade-off:** It is a much larger download and can be significantly slower when installing new packages.
- **Installation:** Continue with the instructions below.

---

## Why do I need this?

In an ideal world, you could download Simmate like any other desktop app and be ready to go. However, Python projects often require specific versions of different tools. For instance:

1. **Simmate** requires Python version 3.11.
2. **Another program** might require an older version, like Python 3.8.

An environment manager (like uv or Anaconda) isolates these projects into separate "folders" or **environments**. This prevents them from conflicting and ensures your software always works as expected.

---

## Installing uv (Recommended)

If you've decided to go with **uv**, follow these steps to get set up. For a complete guide, visit the [official uv installation page](https://docs.astral.sh/uv/getting-started/installation/).

Open your terminal and run the command for your operating system:

=== "macOS & Linux"
    ``` bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"
    ``` powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

After running the command, you may need to restart your terminal for the `uv` command to become available. You can verify it's working by typing `uv --version`.

---

## Installing Anaconda

If you've decided to go with Anaconda, follow these steps to get set up on your local desktop or laptop.

### 1. Download and Install
Visit the [Anaconda download page](https://www.anaconda.com/download) and download the installer for your operating system. You do **not** need to create an account; just run the installer and stick to the default options.

!!! tip
    If you work at a large company (>200 employees), Anaconda requires a paid license. In that case, download [Miniforge](https://github.com/conda-forge/miniforge) instead—it's free, open-source, and works exactly the same way.

### 2. Open Anaconda Navigator
Once installed, launch **Anaconda Navigator**. This is your central hub. On the home screen, you'll see several apps like Jupyter Notebook and Spyder. We'll use these later to write your own Python code.

<p align="center" style="margin-bottom:40px;">
<img src="https://mintlify.s3.us-west-1.amazonaws.com/anaconda-29683c67/images/nav-tabs.png" height=350 style="max-height: 350px;">
</p>

### 3. View Environments
Click the **Environments** tab on the left. You'll see a `base` environment already exists. You can create new ones here, though in the next tutorial, we'll show you how to do this much faster using the command line.

!!! tip
    If you want a more comprehensive overview of Anaconda, they offer a series of [getting-started guides](https://docs.anaconda.com/anaconda/user-guide/). However, these guides aren't necessary for using Simmate (so don't spend more than 10 minutes browsing through them).

---

## Next Steps

Now that you have your manager installed, it's time to learn how to talk to it. Even if you're using Anaconda, the fastest way to work is through the [Command-line](command_line.md).
