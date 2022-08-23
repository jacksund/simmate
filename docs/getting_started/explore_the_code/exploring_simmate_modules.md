
# Exploring Simmate's Modules

Now that we know Simmate is just a bunch of classes organized into folders, let's explore a bit.

We'll start with the `toolkit` module ([here](https://github.com/jacksund/simmate/tree/main/src/simmate/toolkit), but try finding it yourself without the link). When you open it up, you'll see an overview/guide. You can also access this module using `from simmate import toolkit` and getting help directly in spyder.

```
from simmate import toolkit

toolkit  # use ctrl+I before hitting enter
```

A good folder to look through is the `simmate.toolkit.creators` module, which provides many ways to create lattices, sites, and structures (e.g. randomly, random symmetry, etc.) and also incorporates third-party codes.

> :warning: because simmate is still at the early stages, some folders will be more complete than others. Keep this in mind while exploring. If you aren't seeing a guide or documentation, we probably haven't finished that module yet.

Take some time to look through the features and functions. Always feel free to ask if a feature exists, and if not, request one too. Post those questions in our [discussions page](https://github.com/jacksund/simmate/discussions/categories/q-a).

Once you're done exploring, you can move on to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md).
