# Initial Setup & Tour

## Quickstart

1. Initialize your database using the prebuilt option. When prompted, type **yes** to download the prebuilt database.
    ``` bash
    simmate database reset
    ```

    !!! tip
        By default, Simmate uses an **SQLite** database. This is a simple file-based database stored in your configuration directory (usually `~/simmate/`). You can find your settings and database file there!

2. Start the Simmate local web server:
    ``` bash
    simmate run-server
    ```

3. Visit your local dashboard by opening your web browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/). 

4. Take a tour of the user interface! You can now explore the data and apps that come pre-installed.
