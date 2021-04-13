# -*- coding: utf-8 -*-

from pymatgen.core.periodic_table import _pt_data as element_data

new_dict = {}
for e, data in element_data.items():
    new_dict.update(
        {
            e: {
                "Atomic mass": data["Atomic mass"],
                "Atomic no": data["Atomic no"],
                "Name": data["Name"],
            }
        }
    )


import json

with open("test.json", "w") as file:
    json.dump(element_data, file)



import pandas

df = pandas.DataFrame.from_dict(new_dict, orient="index")
df.to_csv("test.csv", index=False)


"""
PyMatGen

from pymatgen.core.periodic_table import Element
e = Element("Ag")

%timeit Element("Ag")
481 ns ± 3.93 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)

%timeit e.symbol
44.1 ns ± 0.296 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

%timeit e.valence
41.1 µs ± 328 ns per loop (mean ± std. dev. of 7 runs, 10000 loops each)

%timeit e.X
197 ns ± 0.292 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)




Simmate

%timeit Element("Ag")
161 ns ± 3.29 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

%timeit e.symbol
40.5 ns ± 0.865 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

%timeit e.number
39.3 ns ± 0.104 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

"""

class Element:
    # pymatgen uses Enum for their base Element class, but it lead's to a bunch of
    # boilerplate code and is also pretty slow to initialize & access attributes.
    # Enum does have the advantage of creating singletons though -- that is, only
    # one instance of given element is ever made. If new ones are produced, they
    # just point to the first instance. This saves on memory in a big way. However,
    # testing shows that this memory only really becomes significant at >100,000,000
    # instances loaded. Before we even reach this point, the lattice and site_coord
    # data will create this memory issue bigger issue. Memory can also be responsibly
    # managed at a higher-level (via unloading/offloading of structures or distribution
    # of many structures with Dask). We therefore opt for speed over memory in this
    # Element class.
    #
    # In the future, I should consider returning to Enum or DataClass implementations
    # of this class though. Other classes to consider are namedspace and namedtuple.
    
    def __init__(self, symbol):
        self.symbol = symbol

        # OPTIMIZE: consider adding key attributes here for optimization.

    def __getattr__(self, item):
        # OPTIMIZE: This function is only called when a "self.item" fails. It therefore
        # takes longer than if you were to set the attribute in the init. However,
        # more often than not, we don't need the attributes set prior. We do this
        # to speed up the initialization of Element objects. This ends up being a
        # problem later if the user is constantly trying to access an attribute that
        # wasn't pre-set. As a potential solution, we could set the attributes as they
        # are accessed -- via the setattr() command. This means the first call takes
        # longer and then it's fast after that. If I never access this attribute again,
        # this is also wasted overhead. I should do more testing as to whether this
        # line is actually beneficial or not.
        setattr(self, item, d[self.symbol][item])
        
        # !!! Do I want to raise an error or just return None if the attr doesn't exist?
        # For the later, I would change the line below to use ".get(item)" instead
        return d[self.symbol][item]
