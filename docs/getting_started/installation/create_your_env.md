# Setting Up Your Environment & Installing Simmate

A virtual environment isolates your Python projects to prevent conflicts between different software versions. We'll use either **uv** or **Anaconda** to manage this.

---

## 1. Environment Creation

Choose your preferred tool to create an environment. You can name it anything (e.g., `my_env`), but use underscores instead of spaces.

=== "uv (Recommended)"
    ``` bash
    uv venv my_env
    ```

=== "conda"
    ``` bash
    conda create -n my_env -c conda-forge python=3.11
    ```

---

## 2. Environment Activation

Switch to your new environment:

=== "uv"
    ``` bash
    source my_env/bin/activate  # On Windows use: my_env\Scripts\activate
    ```

=== "conda"
    ``` bash
    conda activate my_env
    ```

If you activated your environment successfully, the start of your terminal line will change to show your environment name — for example, `(my_env)`.

---

## 3. Simmate Installation

With your environment active, install the Simmate package:

=== "uv"
    ``` bash
    uv pip install simmate
    ```

=== "conda"
    ``` bash
    conda install -c conda-forge simmate
    ```

---

## 4. IDE Installation (Optional)

If you're new to coding, we recommend the [Spyder IDE](https://www.spyder-ide.org/) for writing Python code. 

=== "uv / pip"
    1. Download and run the **Standalone Installer** from the [Spyder website](https://www.spyder-ide.org/).
    2. In your `my_env` terminal, install the `spyder-kernels` package:
        ``` bash
        uv pip install spyder-kernels
        ```
    3. Once both are installed, you'll need to point Spyder to your `my_env` Python interpreter. We'll cover this in a later tutorial.

=== "conda"
    You can install Spyder directly into your environment:
    ``` bash
    conda install -c conda-forge spyder
    ```

---
