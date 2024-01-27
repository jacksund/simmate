# Launching Your Local Test Server

Our official website allows you to view all past workflow results. Even if you haven't run any workflows yet, you can replicate this on your local computer using two simple commands.

----------------------------------------------------------------------

## 1. Reset the Database

Firstly, we need to configure our database. We'll delve into the specifics in a following tutorial, but for now, consider this as creating an empty Excel spreadsheet that we'll populate with data later. This can be done with...

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

... and after a few moments, you should see the following output:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Keep this command running in your terminal and open the link [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your preferred browser (Chrome, Firefox, etc.). You should see a site that resembles the simmate.org website! 

----------------------------------------------------------------------

## Final comments

The server we just started is hosted on your local computer. It's not accessible via the internet, and it will cease to function as soon as you close your terminal running the `simmate run-server` command. However, when we transition to a server that's accessible via the internet, Simmate's full set of features become available. This allows you to share results and computational resources with your entire team & accross many computers.

Additionally, keep in mind that Simmate's Python and command-line interfaces offer many more features than what is available in the website. To learn about these features, continue reading our tutorials!

----------------------------------------------------------------------
