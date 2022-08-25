
# Starting your local test server

On our official website, you are able to explore all results from past workflows that we've ran. Even though you haven't ran any yet, you can do the same thing on your local computer too. All that's required are two simple commands.

First, we need to setup our database. We'll explain what this is doing in the next tutorial, but for now, think of this as building an empty excel spreadsheet that we can later fill with data. This is done with...

``` bash
simmate database reset # (1)
```

1. When prompted, you can confirm that you want to reset/delete your "old" database. Also agree to download and use a prebuilt database.

!!! tip
    Unless you want to remove all of your data and start from scratch, you'll never have to run that command again.

And then as our second step, we simply tell Simmate to start the server:

``` bash
simmate run-server
```

... and after a few seconds, you should see the output ...

``` bash
Watching for file changes with StatReloader
April 05, 2022 - 00:06:54
Django version 4.0.2, using settings 'simmate.configuration.django.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Leave this command running in your terminal and open up the link [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your preferred browser (Chrome, Firefox, etc.). You should see what looks like the simmate.org website! 

However, **this website is running on your local computer and won't contain any data yet**. No one can access it through the internet, and as soon as your close your terminal running the `simmate run-server`, this site will stop working.

Simmate becomes especially powerful when we switch to a server that accessible through the internet -- that way, you can share results and computational resources with your entire team. Also, there are many more features in python and command-line than through the website interface. To explore these, you'll have to keep reading our tutorials! 
