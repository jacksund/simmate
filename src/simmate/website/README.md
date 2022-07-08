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

For option 3, we have [a guide for setting a server up on DigitalOcean](https://github.com/jacksund/simmate/tree/main/.do). In addition to this guide, make sure you complete the base simmate tutorials -- and pay particular attention to the tutorials on [setting up a cloud database](https://github.com/jacksund/simmate/blob/main/tutorials/07_Use_a_cloud_database.md) and [setting up computational resources](https://github.com/jacksund/simmate/blob/main/tutorials/08_Add_computational_resources.md).


## The REST API

**This is only for experts! If you are trying to pull data from Simmate, then you should instead  use our python client that is introduced in [the database tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md). Grabbing data directly from our REST API is really only for teams that can't use python or Simmate's code but still want to pull data. Also note that grabbing data via our REST API is heavily throttled, so this is not a good way to grab large amounts of data.**

While the accronym may not be super intuitive for beginners, "REST API" stands for "**Re**presentational **s**tate **t**ransfer (REST) **A**pplication **P**rogramming **I**nterfaces (API)". In simple terms, this is how we can access databases from a website url. 

The easiest way to understand our API is with some examples. In the examples below, we only look at the Materials Project database (at [`/third-parties/MatprojStructure/`](http://simmate.org/third-parties/MatprojStructure/)), but in addition to this example, nearly every URL within Simmate has REST API functionality! Our API endpoints are automatically built from our database module -- so it's very easy to implement new features and add new tables.


### Accessing the API

Let's start with a normal URL and webpage:
```
http://simmate.org/third-parties/MatprojStructure/
```

When you open that link, you are brought to a webpage that let's you search through all Materials Project structures. Under the hood, this URL is actually a REST API too! All we have to do is add `?format=api` to the end of the URL. Try opening this webpage:
```
http://simmate.org/third-parties/MatprojStructure/?format=api
```

Likewise, if we use `?format=json`, we can get our data back as a JSON dictionary:
```
http://simmate.org/third-parties/MatprojStructure/?format=json
```

The same can be done for individual entries too! For example, if we wanted all the data for the structure with id `mp-1`, then we can do...
```
http://simmate.org/third-parties/MatprojStructure/mp-1/?format=api
http://simmate.org/third-parties/MatprojStructure/mp-1/?format=json
```

For these, you should see an output similar too...
``` json
{
    "id": "mp-1",
    "structure_string": "...(truncated for clarity)",
    "nsites": 1,
    "nelements": 1,
    "elements": ["Cs"],
    "chemical_system": "Cs",
    "density": 1.9350390306525629,
    "density_atomic": 0.00876794537479071,
    "volume": 114.05180544066401,
    "volume_molar": 68.68360262958124,
    "formula_full": "Cs1",
    "formula_reduced": "Cs",
    "formula_anonymous": "A",
    "energy": -0.85663276,
    "energy_per_atom": -0.85663276,
    "energy_above_hull": null,
    "is_stable": null,
    "decomposes_to": null,
    "formation_energy": null,
    "formation_energy_per_atom": null,
    "spacegroup": 229,
}
```

This is super useful because we can grab data from any programming language we'd like -- python, javascript, c++, fortran, or even the command-line. The only requirement to use our REST API is that you have access to the internet! Once you load your desired data, what you do with the JSON output is up to you.


### Filtering results

Our URLs also support complex filtering too. As an example, let's make a search where we want all structures that have the spacegroup 229 and also are in the Cr-N chemcial system. When you make this search in the normal webpage, you'll notice the URL becomes...
```
http://simmate.org/third-parties/MatprojStructure/?chemical_system=Cr-N&spacegroup__number=229
```

We specify our conditions by adding a question mark (`?`) at the end of the URL and then adding `example_key=desired_value` after that. As we add new conditions, we separate them with `&` -- which results in `key1=value1&key2=value2&key3=value3` and so on. You can also add `format=api` at the end of this too!

Note, our python client for accessing data is MUCH more powerful for filtering through results, so we recommend accessing data using the `simmate.database` module in complex/advanced cases.


### Paginating results

To protect our servers from overuse, Simmate currently returns a maximum of 12 results at a time. Pagination is handled automitically using the `page=...` keyword in the URL. In the HTML, API, and JSON views, you should always have the link to the next page of results available. For example in the JSON view, the returned data includes `next` and `previous` URLs.


### Ordering results

For API and JSON formats, you can manually set the ordering of returned data by adding `ordering=example_column` to your URL. You can also reverse the ordering with `ordering=-example_column` (note the "`-`" symbol before the column name). For example:

```
http://simmate.org/third-parties/MatprojStructure/?ordering=density_atomic
```

### The API for experts

We build Simmate's REST API using the [django-rest-framework](https://www.django-rest-framework.org/) python package, and implement filtering using [django-filter](https://django-filter.readthedocs.io/en/stable/). 

Our endpoints are NOT fixed but are instead dynamically created for each request. This is thanks to our `SimmateAPIViewset` class in the `simmate.website.core_components` module, which takes a Simmate database table and automatically renders an API endpoint for us. The backend implementation of dynamic APIs is still experimental because we are exploring the pros and cons the approach -- for example, this enables quick start-up times for configuring Django, but also comes at the cost of more CPU time per web request.


## CSS and JS assets

Simmate does not distribute the majority of source CSS and JavaScript files because we use assets from a third-party vendor and redistribution is not allowed under their licensing. Specifically, we use the [Hyper theme](https://themes.getbootstrap.com/product/hyper-responsive-admin-dashboard-template/) from the [CoderThemes team](https://coderthemes.com/). Using the subpages and guides available on their [Modern Dashboard template](https://coderthemes.com/hyper/modern/index.html), you'll be able to contribute to Simmate's website without needing to access any of the assets. Within our templates, you'll note we always load assets from a Simmate CDN:

``` html
<!-- How an asset is normally loaded when distributed with source code -->
<link href="assets/css/vendor/fullcalendar.min.css" rel="stylesheet" type="text/css" />

<!-- How assets are loaded for Simmate using our CDN -->
<link href="https://archives.simmate.org/assets/fullcalendar.min.css" rel="stylesheet" type="text/css" />
```

If you ever need to alter the CSS or JS, please reach out to our team so we can discuss the best way to approach this.


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
