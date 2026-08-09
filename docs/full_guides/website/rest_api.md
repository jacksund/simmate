# Simmate REST API

!!! warning
    **This section is for developers and advanced users.** 
    If you are using Python, we strongly recommend using the [Simmate Python Client](/full_guides/database/basic_use.md) instead. The REST API is primarily for teams that cannot use our Python package but still need to extract data. **Note:** Data extraction via the REST API is heavily throttled and not suitable for large-scale data retrieval.

------------------------------------------------------------

## Overview

The Simmate REST API allows you to access database tables directly through URL endpoints. It follows REST principles and returns data in structured JSON format. 

To explore the API, you can use the Materials Project dataset as an example:

- **Web View**: [simmate.org/data/MatprojStructure/](http://simmate.org/data/MatprojStructure/)
- **API View**: [simmate.org/data/MatprojStructure/?format=json](http://simmate.org/data/MatprojStructure/?format=json)

Nearly every URL in Simmate's **Data** tab supports this functionality.

--------------------------

## Basic Usage

To retrieve data as JSON, append `?format=json` to any data URL.

### Browsing a table
To list entries from a table, use the base table URL:
```text
http://simmate.org/data/MatprojStructure/?format=json
```

**Example Table JSON Response:**
```json
{
    "count": 154718,
    "next": "http://simmate.org/data/MatprojStructure/?format=json&page=2",
    "previous": null,
    "results": [
        {
            "id": "mp-1",
            "formula_full": "Cs1",
            "spacegroup": 229,
            ...
        },
        ...
    ]
}
```

### Accessing a single entry
To access all data for a specific entry (e.g., id `mp-1`):
```text
http://simmate.org/data/MatprojStructure/mp-1/?format=json
```

**Example Entry JSON Response:**
```json
{
    "id": "mp-1",
    "structure": "...(structure data)...",
    "nsites": 1,
    "nelements": 1,
    "elements": ["Cs"],
    "chemical_system": "Cs",
    "density": 1.935,
    "formula_full": "Cs1",
    "spacegroup": 229,
    ...
}
```

--------------------------

## Filtering Results

Simmate supports advanced filtering using [Django ORM lookup syntax](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#field-lookups).

### Field Lookups
Use double underscores (`__`) to perform specific comparisons:

- **Range**: `energy_per_atom__gte=-5.0` (Greater than or equal to)
- **Nullity**: `description__isnull=True`
- **Text**: `formula_full__icontains=Fe` (Case-insensitive search)

### Chaining Relations
You can also filter across database relationships:

- `user__username=jacksund`
- `user__first_name__isnull=False`

!!! note
    To maintain server performance, some Simmate servers limit the number of double underscores allowed in a single filter. For instance, **simmate.org has a limit of 3** (e.g., `a__b__c__d` is okay, but `a__b__c__d__e` is not). This prevents excessively complex database joins.

### Complete Example
Search for structures with spacegroup 229 in the Cr-N chemical system:
```text
http://simmate.org/data/MatprojStructure/?chemical_system=Cr-N&spacegroup__number=229&format=json
```

--------------------------

## Pagination & Ordering

### Pagination
To avoid server overload, results are limited to 12 per page. Navigate using the `page` parameter:
```text
http://simmate.org/data/MatprojStructure/?format=json&page=2
```
The response includes `next` and `previous` links to help you traverse the dataset.

### Ordering
Order results by any column using the `ordering` parameter. Use a minus sign (`-`) for descending order:
```text
http://simmate.org/data/MatprojStructure/?ordering=-density&format=json
```

--------------------------

## Authentication

### Public Website (simmate.org)
Public endpoints on simmate.org do not require authentication for anonymous browsing.

=== "python requests"
    ```python
    import requests
    url = 'http://simmate.org/data/MatprojStructure/?format=json'
    response = requests.get(url)
    print(response.json())
    ```

=== "curl"
    ```bash
    curl -X GET http://simmate.org/data/MatprojStructure/?format=json
    ```

### Private Servers
Private or team-managed servers may require an API key, which can be found on your **Profile** page. Include the key in your request header:

=== "python requests"
    ```python
    import requests
    url = 'http://my-server.org/data/MyTable/?format=json'
    headers = {'Authorization': 'Token YOUR_API_KEY_HERE'}
    response = requests.get(url, headers=headers)
    print(response.json())
    ```

=== "curl"
    ```bash
    curl -X GET http://my-server.org/data/MyTable/?format=json \
         -H "Authorization: Token YOUR_API_KEY_HERE"
    ```
