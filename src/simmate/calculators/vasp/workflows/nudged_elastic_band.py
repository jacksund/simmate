# -*- coding: utf-8 -*-

"""
Nudged elastic band is composed of the following stages...

1. Relax the starting bulk structure

2. Identify all symmetrically unique pathways

*** and then the remaindering steps are done for each individual pathway ***

3. Relax the start/end supercell images 
    (or only one of these if they are equivalent)

4. Interpolate the start/end supercell images and empirically relax these
    using IDPP.

5. Relax all images using NEB

And some helpful links for running VASP:

- [VASP's guide for NEB](https://www.vasp.at/wiki/index.php/TS_search_using_the_NEB_Method)
- [Plug-in guide for CI-NEB](https://theory.cm.utexas.edu/vtsttools/neb.html)
- [PyMatGen namespace for NEB with VASP](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/io.py)


For this overall workflow, a user may want to start at a different step -- for 
example, they could have a specific start/end structure that they want to provide
rather than having automatically detection of unique pathways. Therefore, we break
this workflow in multiple smaller ones. We must account for the following input
scenarios:

1. `neb_all_paths`: a bulk crystal + diffusing species is given and full analysis of all paths is 
requested

2. `neb_single_path`: a bulk crystal + diffusing species + pathway index is given, where index gives
the specific pathway to be grabbed from DistinctPathFinder

3. `neb_from_indices`: a bulk crystal + start/end index for diffusing ion is given and that specific
pathway should be analyzed 

4. `neb_from_endpoints`: two endpoint supercell structures are given and that specific
pathway should be analyzed 

5. `neb_from_images`: a series of images are given and that specific pathway should be analyzed


On top of these 5 scenarios, I should also consider...
- vacancy vs. interstitial diffusion
- plugins for CI-NEB

"""
