# Launching Your Local Test Server

Our official website allows you to view all past workflow results. Even if you haven't run any workflows yet, you can replicate this on your local computer using two simple commands.

----------------------------------------------------------------------

## 1. Reset the Database

Firstly, we need to configure our database. We'll delve into the specifics in the next tutorial, but for now, consider this as creating an empty Excel spreadsheet that we'll populate with data later. This can be done with...

``` bash
simmate database reset # (1)
```

1. When prompted, confirm that you wish to reset/delete your "old" database. Also, agree to download and utilize a prebuilt database.

!!! tip
    You won't need to run this command again unless you want to erase all your data and start anew.

----------------------------------------------------------------------

## 2. Start the Server

For our second step, we simply instruct Simmate to launch the server:

``` bash
simmate run-server
```

... and after a few moments, you should see the following output ...

``` bash
Watching for file changes with StatReloader
April 05, 2022 - 00:06:54
Django version 4.0.2, using settings 'simmate.configuration.django.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Keep this command running in your terminal and open the link [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your preferred browser (Chrome, Firefox, etc.). You should see a site that resembles the simmate.org website! 

----------------------------------------------------------------------

## Can I Share These Links?

**This website is hosted on your local computer**. It's not accessible via the internet, and it will cease to function as soon as you close your terminal running the `simmate run-server` command.

However, Simmate's true potential is unleashed when we transition to a server that's accessible via the internet. This allows you to share results and computational resources with your entire team. Additionally, Python and command-line offer many more features than the website interface. To discover these, continue reading our tutorials! 

----------------------------------------------------------------------