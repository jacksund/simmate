
This module is analogous to `matminer.data_retrieval` and `pymatgen.ext` modules, where we are pulling data from third-party databases.


Note, that the structures we pull into our database may not be exact matches to
what's shown in their database. This is beacuse we run symmetry analysis on the
structure and convert to a LLL reduced cell.


_**WARNING:**_ If you are trying to use Simmate to pull various data from Materials Project, OQMD, AFLOW, and others *into your own project/script/analysis*, you should jump over to the `simmate.database` module! This module is for pulling data from various databases *into the Simmate database*. Therefore, you should only be using this module if you are on Simmate development team or an expert user.


Many of the providers Simmate pulls data from have a preferred way to access their data and some even have multiple options. When deciding how we pull data from each, we prefer to ask providers directly and then we rank Simmate's preferred method on this list:


1. **Custom python package.** Other teams have put a lot of work into efficiently using their data. If their package is well managed and makes our lives easier, then we should use it! A great example of this is the MPRester class in pymatgen, which we use to pull Material Project data. The caveat here is that we have to install the extra package. We therefore list
these as optional dependencies in the Simmate code -- as they aren't used anywhere else in our code.

2. **REST API or GraphQL.** If the provider has a web interface, we can easily pull their data using the python `requests` package. In many cases, a REST API is an inefficient way to pull data - as it involves querying their database thousands of times -- potentially crashing their server. In cases like that, we actually prefer a download file (option 4, shown below).

3. **OPTIMADE endpoint.** This is a standardized REST API endpoint that many databases are using now. The huge upside here is that each database will have a matching API. The downside is that OPTIMADE doesn't have a good way to pull data in bulk. Their team is currently working on this though, and we many bump the priority of this approach in the future.

4. **Download compressed file.** If the database provider provides a dump file (typically a *.zip file), then we can use that! This is typically a slower setup, but it can be much easier on the provider's servers (see comment in option 2, shown above).

5. **Web scraping.** As an absolute last resort, we can use `requests` to scrape webpages for data (or `selenium` in even more extreme cases.). This requires the most work from our team and is also the least efficient way to grab data. Therefore, scraping should always be avoided if possible.
