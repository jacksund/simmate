# Launching Your Local Test Server

Our official website allows you to view datasets, such all your past workflow results or downsets that you've download from other sources. We haven't loaded any data yet, but you can still start up the website on your local computer using two simple commands.

----------------------------------------------------------------------

## 1. Reset the Database

Firstly, we need to configure our database. We'll explain this more in a following tutorial, but for now, consider this as creating an empty Excel spreadsheet that we'll populate with data later. This can be done with:

``` bash
simmate database reset
```

When prompted, confirm that you want to reset/delete your "old" database. Also, agree to download and use a prebuilt database.

!!! tip
    You won't need to run this command again unless you want to erase all your data and start anew. Ideally, you have a single database that grows over time. But still, sometimes it's good to start from scratch when you're testing things out, so this `reset` command is handy in those cases.

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

**Keep this command running** in your terminal and open the link [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your preferred browser (Chrome, Firefox, etc.). You should see a site that resembles the simmate.org website!

!!! tip
    The `simmate run-server` command will run forever if you let it. To stop it, use `crtl+c` or close your terminal window completely. Once stopped, you'll see that the website stops working in your browser as well.

----------------------------------------------------------------------

## Final comments

The server we just started is hosted on your local computer. It's not accessible via the internet, and it will cease to function as soon as you close your terminal running the `simmate run-server` command. However, when we switch to a server that's accessible via the internet, Simmate's full set of features become available. This allows you to share results and computational resources with your entire team & accross many computers. This is covered in a later tutorial.

Additionally, keep in mind that Simmate's Python and command-line interfaces offer many more features than what is available in the website. To learn about these features, continue reading our tutorials!

----------------------------------------------------------------------
