# The Simmate Website

This module hosts everything for the website interface and API. Unlike other major projects, Simmate makes our website's source-code openly available to everyone! This means that you can host your own Simmate website on your own computer or even in production for your lab to privately use.


## Running a server locally

You can quickly get Simmate up-and-running on your local computer using the command...
``` bash
# set up your database if you haven't done so already
simmate database reset

# now run the website locally!
simmate run-server
```

While this command is running, open up your preferred browser (Chrome, Firefox, etc.) and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/). While this looks just like our actaul website at `simmate.org`, this one is running locally on your desktop and using your personal database!


## Running a production-ready server

To have everything set up for your team, you can do one of the following...

1. ask about collaborating with the Simmate team and join our server
2. ask about having our team manage a server for you
3. set up and manage your own server

For options 1 and 2, just send us an email at `simmate.team@gmail.com`.

For option 3, we have [a guide for setting a server up on DigitalOcean](https://github.com/jacksund/simmate/tree/main/.do). In addition to this guide, make sure you complete the base simmate tutorials -- and pay particular attention to the tutorials on [setting up a cloud database](https://github.com/jacksund/simmate/blob/main/tutorials/08_Use_a_cloud_database.md) and [setting up computational resources](https://github.com/jacksund/simmate/blob/main/tutorials/09_Add_computational_resources.md).

## Third-party sign ins

Simmate supports signing into the website via third-party accounts such as Google and Github. This functionality is thanks to the [`django-allauth`](https://github.com/pennersr/django-allauth) package.

By default, servers will not display these sign-in buttons, so if you wish to configure logins for third-party accounts, you must do this manually. While there are many types of accounts that can be used with `django-allauth` (see their [full list](https://django-allauth.readthedocs.io/en/latest/providers.html)), Simmate only supports Github and Google at the moment. We give guides on how to set these up below.

### Github OAuth

1. Create a new OAuth application with [this link](https://github.com/settings/applications/new) and the following information (note we are using `http://127.0.0.1:8000`, which is your local test server. Replace this with the link to your cloud server if it's available.):
    - application name = My New Simmate Server (edit if you'd like)
    - homepage url = http://127.0.0.1:8000
    - authorization callback url = http://127.0.0.1:8000/accounts/github/login/callback/

2. On the next page, select "Generate a new client secret" and copy this value to your clipboard.

3. On your local computer (or production-ready server), set the environment variables:
    - GITHUB_SECRET = examplekey1234 (value is what you copied from step 2)
    - GITHUB_CLIENT_ID = exampleid1234 (value is listed on github as "Client ID")


### Google OAuth

1. Follow steps from django-allauth ([here](https://django-allauth.readthedocs.io/en/latest/providers.html#google)) to configure the Google API application
2. On your local computer (or production-ready server), set the environment variables:
    - GOOGLE_SECRET = examplekey1234
    - GOOGLE_CLIENT_ID = exampleid1234

## CSS and JS assets

Simmate does not distribute the majority of source CSS and JavaScript files because we use assets from a third-party vendor and redistribution is not allowed under their licensing. Specifically, we use the [Hyper theme](https://themes.getbootstrap.com/product/hyper-responsive-admin-dashboard-template/) from the [CoderThemes team](https://coderthemes.com/). Using the subpages and guides available on their [Modern Dashboard template](https://coderthemes.com/hyper/modern/index.html), you'll be able to contribute to Simmate's website without needing to access any of the assets. Within our templates, you'll note we always load assets from a Simmate CDN:

``` html
<!-- How an asset is normally loaded when distributed with source code -->
<link href="assets/css/vendor/fullcalendar.min.css" rel="stylesheet" type="text/css" />

<!-- How assets are loaded for Simmate using our CDN -->
<link href="https://archives.simmate.org/assets/fullcalendar.min.css" rel="stylesheet" type="text/css" />
```

If you ever need to alter the CSS or JS, please reach out to our team so we can discuss the best way to approach this.
