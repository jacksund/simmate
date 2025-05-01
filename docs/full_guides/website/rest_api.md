# Simmate REST API

!!! warning
    This section is only for experts! If you're aiming to extract data from Simmate, we suggest using our Python client, as outlined in [the database guides](/full_guides/database/overview.md). The REST API is mainly for teams that cannot use Simmate's python package but still need to extract data. Be aware that data extraction via our REST API is heavily throttled, making it unsuitable for large data retrievals.

------------------------------------------------------------

## About

"REST API" stands for "**Re**presentational **S**tate **T**ransfer (REST) **A**pplication **P**rogramming **I**nterfaces (API)". In simpler terms, it's a way to access databases through a website URL.

------------------------------------------------------------

## Example Endpoint

To better understand our API, we'll use the Materials Project data as an example. You can view this data at [`/data/MatprojStructure/`](http://simmate.org/data/MatprojStructure/). Keep in mind, nearly every URL within Simmate's `Data` tab has REST API functionality and behaves the same as this dataset.

------------------------------------------------------------

## API Usage

Consider a typical URL and webpage:
```
http://simmate.org/data/MatprojStructure/
```

This link takes you to a webpage where you can browse all Materials Project structures. However, this URL also serves as a REST API. To access it, simply add `?format=api` to the URL. Try this link:
```
http://simmate.org/data/MatprojStructure/?format=api
```

Likewise, adding `?format=json` will return data in a JSON dictionary:
```
http://simmate.org/data/MatprojStructure/?format=json
```

This also applies to individual entries. For example, to access all data for the structure with id `mp-1`, use...
```
http://simmate.org/data/MatprojStructure/mp-1/?format=api
http://simmate.org/data/MatprojStructure/mp-1/?format=json
```

The output should look like...
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

------------------------------------------------------------

## Filtering Results

Our URLs also support advanced filtering. For instance, to search for all structures with the spacegroup 229 in the Cr-N chemical system, the URL becomes...
```
http://simmate.org/data/MatprojStructure/?chemical_system=Cr-N&spacegroup__number=229
```

Conditions are specified by adding a question mark (`?`) to the URL, followed by `example_key=desired_value`. Additional conditions are separated by `&`, resulting in `key1=value1&key2=value2&key3=value3`, etc. You can also add `format=api` to this.

However, for complex or advanced cases, we recommend using the `simmate.database` module, as it provides more robust filtering capabilities.

------------------------------------------------------------

## Pagination of Results

To avoid server overload, Simmate currently returns a maximum of 12 results at a time. Pagination is automatically managed using the `page=...` keyword in the URL. In the HTML, API, and JSON views, links to the next page of results are always provided. For instance, in the JSON view, the returned data includes `next` and `previous` URLs.

------------------------------------------------------------

## Ordering Results

You can set the order of returned data by adding `ordering=example_column` to your URL. To reverse the order, use `ordering=-example_column` (note the "`-`" before the column name). For example:

```
http://simmate.org/data/MatprojStructure/?ordering=density_atomic
```

------------------------------------------------------------

## Programmer access & API Keys

### Public Website
The public Simmate website does not require you to be authenticated to access our API endpoints. You can therefore call API endpoints anonymously:

=== "python requests"

    ```python
    import requests

    url = 'http://simmate.org/data/MatprojStructure/?format=json'
    response = requests.get(url)

    print(response.text)
    ```

=== "curl"
    ``` bash
    curl -X GET http://localhost/data/CortevaTarget/?format=api
    ```

### Private Servers

Some custom servers (such as Simmate's Corteva site), do require authenticated users to ensure data secuirity. For these, you can access endpoints by providing an API key.

1. find your API key in the `Profile` page of the website and select the `View API Key` at the bottom of the page. The key will be something like...
```
59ced7225bb41d51b7bc78c1e269542eaa99c72f
```

2. make sure you provide the API as a header in your requests:

    === "python requests"

        ```python
        import requests

        url = 'http://simmate.org/data/MatprojStructure/?format=json'
        headers = {'Authorization': 'Token 59ced7225bb41d51b7bc78c1e269542eaa99c72f'}

        response = requests.get(url, headers=headers)

        print(response.text)
        ```

    === "curl"
        ``` bash
        curl -X GET http://simmate.org/data/MatprojStructure/?format=json -H 'Authorization: Token 59ced7225bb41d51b7bc78c1e269542eaa99c72f'
        ```

------------------------------------------------------------

## Advanced API Usage

Our endpoints are dynamically created for each request, thanks to our `SimmateAPIViewset` class in the `simmate.website.core_components` module, which automatically renders an API endpoint from a Simmate database table. The backend implementation of dynamic APIs is still experimental as we assess the pros and cons of this approach -- for example, it allows for quick Django configuration, but at the expense of increased CPU time per web request.

------------------------------------------------------------
