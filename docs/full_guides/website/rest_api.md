
# The REST API

!!! warning
    This section is only for experts! If you are trying to pull data from Simmate, then you should instead  use our python client that is introduced in [the database guides](/full_guides/database/overview/). Grabbing data directly from our REST API is really only for teams that can't use python or Simmate's code but still want to pull data. Also note that grabbing data via our REST API is heavily throttled, so this is not a good way to grab large amounts of data.

While the accronym may not be super intuitive for beginners, "REST API" stands for "**Re**presentational **s**tate **t**ransfer (REST) **A**pplication **P**rogramming **I**nterfaces (API)". In simple terms, this is how we can access databases from a website url. 


## Our example endpoint

The easiest way to understand our API is with some examples. In the examples below, we only look at the Materials Project database (at [`/third-parties/MatprojStructure/`](http://simmate.org/third-parties/MatprojStructure/)), but in addition to this example, nearly every URL within Simmate has REST API functionality! Our API endpoints are automatically built from our database module -- so it's very easy to implement new features and add new tables.


## Accessing the API

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
    "structure": "...(hidden for clarity)",
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


## Filtering results

Our URLs also support complex filtering too. As an example, let's make a search where we want all structures that have the spacegroup 229 and also are in the Cr-N chemcial system. When you make this search in the normal webpage, you'll notice the URL becomes...
```
http://simmate.org/third-parties/MatprojStructure/?chemical_system=Cr-N&spacegroup__number=229
```

We specify our conditions by adding a question mark (`?`) at the end of the URL and then adding `example_key=desired_value` after that. As we add new conditions, we separate them with `&` -- which results in `key1=value1&key2=value2&key3=value3` and so on. You can also add `format=api` at the end of this too!

Note, our python client for accessing data is MUCH more powerful for filtering through results, so we recommend accessing data using the `simmate.database` module in complex/advanced cases.


## Paginating results

To protect our servers from overuse, Simmate currently returns a maximum of 12 results at a time. Pagination is handled automitically using the `page=...` keyword in the URL. In the HTML, API, and JSON views, you should always have the link to the next page of results available. For example in the JSON view, the returned data includes `next` and `previous` URLs.


## Ordering results

For API and JSON formats, you can manually set the ordering of returned data by adding `ordering=example_column` to your URL. You can also reverse the ordering with `ordering=-example_column` (note the "`-`" symbol before the column name). For example:

```
http://simmate.org/third-parties/MatprojStructure/?ordering=density_atomic
```

## The API for experts

We build Simmate's REST API using the [django-rest-framework](https://www.django-rest-framework.org/) python package, and implement filtering using [django-filter](https://django-filter.readthedocs.io/en/stable/). 

Our endpoints are NOT fixed but are instead dynamically created for each request. This is thanks to our `SimmateAPIViewset` class in the `simmate.website.core_components` module, which takes a Simmate database table and automatically renders an API endpoint for us. The backend implementation of dynamic APIs is still experimental because we are exploring the pros and cons the approach -- for example, this enables quick start-up times for configuring Django, but also comes at the cost of more CPU time per web request.
