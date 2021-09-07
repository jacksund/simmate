
# The REST API for Simmate

**This page is only for experts! If you are trying to pull data from Simmate, then you should instead  use our [python client](). Grabbing data directly from our REST API is really only for teams that can't use python or Simmate codes but still want to pull our data. Also note that grabbing data via our REST API is heavily throttled, so this is not a good way to grab large amounts of data.**


REST APIs are "**Re**presentational **s**tate **t**ransfer (REST) methods a **A**pplication **P**rogramming **I**nterfaces (API)".


In simple terms, this is how we can access databases from a website url. For example, if I were to go to [www.simmate.org/rest-api/simmate/sm-1](http://127.0.0.1:8000/rest-api/jarvis/jvasp-90856/), then that link would send me back the data relating to the sm-1 structure. REST APIs typically send the data back as a JSON file. Try clicking the link above to see what you get! It should look like this:
```
{
    "url": "http://127.0.0.1:8000/rest-api/jarvis/jvasp-90856/",
    "structure_string": "Ti2 Cu2 Si2 As2....(truncated for clarity)",
    "nsites": 8,
    "nelement": 4,
    "chemical_system": "As-Cu-Si-Ti",
    "density": 5.956099100023135,
    "molar_volume": 9.0000223436959,
    "spacegroup": 129,
    "formula_full": "Ti2 Cu2 Si2 As2",
    "formula_reduced": "TiCuSiAs",
    "formula_anonymous": "ABCD",
    "formation_energy_per_atom": -0.42762,
    "energy_above_hull": 2103.442283333333
}
```


This is super useful because we can grab data from any programming language we'd like -- python, javascript, c++, fortran, or even the command-line. The only requirement to use someone's REST API is that you have access to the internet! Once you load some data,
what you do with the JSON output is up to you.

We build Simmate's REST API using the [django-rest-framework](https://www.django-rest-framework.org/) python package, which takes very little to setup (that's why there are only two files here). We can also access some advanced filtering thanks to [django-filter](https://django-filter.readthedocs.io/en/stable/). Let's look at some examples of filtering. In every example, we filter off results by adding a question-mark plus any criteria we'd like. For example, our final url will look like...
**www.simmate.org/rest-api/simmate/?some_property=some_target_value**


### Grabbing structures in a chemical system
First, let's grab all structures that are in the "Li-Co-O" system. Note that we need
to be careful here and specify our elements in alphabetical order (Co-Li-O): [http://simmate.org/rest-api/simmate/?chemical_system=Co-Li-O](http://127.0.0.1:8000/rest-api/materials-project/?chemical_system=Co-Li-O)
This can be done with any field too (nsites, nelement, chemical_system, formula_anonymous, etc.).

### Grabbing structures that meet multiple criteria
Now, let's chain multiple criteria together! We do this with the **&** symbol. Let's limit our Li-Co-O search to just structures with spacegroup number 166: [http://simmate.org/rest-api/simmate/?chemical_system=Co-Li-O&space_group=166](http://127.0.0.1:8000/rest-api/materials-project/?chemical_system=Co-Li-O&space_group=166)

### Using conditional filtering criteria
What if we now want to limit our search to structures below 50meV hull energy? Setting an exact value won't work for us anymore. Instead we now want to a search that says "filter for structures that have energy_above_hull less than or equal to 50". While our python client can handle this scenario with ease (by using "__lte" for "less than or equal to" --> we'd use energy_above_hull__lte=50), our REST API cannot yet handle this scenario. This would require more setup on our end, which we choose not to support because we want to limit when users access the REST API. If you are filtering off structures with diverse criteria OR need to pull a large number of structures, please use our [python client]() instead.
