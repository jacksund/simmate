# Nudged Elastic Band (NEB)

NEB is a method of finding the energy barrier for a specific migration pathway, such as atomic diffusion.

## Nudged elastic band is composed of the following stages

** Note: Steps 3-5 are done for each individual pathway **

1. Relax the starting bulk structure

2. Identify all symmetrically unique pathways

3. Relax the start/end supercell images 
    (or only one of these if they are equivalent)

4. Interpolate the start/end supercell images and empirically relax these
    using IDPP.

5. Relax all images using NEB


## Possible inputs

For this overall workflow, a user may want to start at a different step. For example, they could have a specific start/end structure that they want to provide rather than using automatic detection of unique pathways. Therefore, we break this workflow in multiple smaller ones. We must account for the following input scenarios:

1. `all_paths`: a bulk crystal + diffusing species is given and full analysis of all paths is requested

2. `single_path`: a bulk crystal + diffusing species + pathway index is given, where index gives the specific pathway to be grabbed from DistinctPathFinder. For example, DistinctPathFinder would find 5 symmetrically unique paths, and you say "I want to run the pathway that is 4th in this list (aka the 4th shortest pathway)"

3. `from_startend_sites`: a bulk crystal + start/end sites for the diffusing ion is given and that specific pathway should be analyzed. For example, this would allow a diffusion pathway that goes from a site at (0,0,0) to (1,1,1).

4. `from_endpoints`: two endpoint supercell structures are given and that specific pathway (from interpolated structures) should be analyzed

5. `from_images`: a series of images are given and analyzed


In additon to these these 5 scenarios, we also consider...

- vacancy vs. interstitial diffusion
- plugins for CI-NEB (not implemented at the moment)


## Helpful links

- [Atomate NEB yaml](https://github.com/hackingmaterials/atomate/blob/main/atomate/vasp/workflows/base/library/neb.yaml)
- [Atomate NEB py](https://github.com/hackingmaterials/atomate/blob/b9ad04e3ae892c51ba2e4d5c045db1c563f287f4/atomate/vasp/workflows/base/neb.py#L10)
- [pymatgen-diffusion neb](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/io.py)
- [pymatgen-diffusion pathfinder](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/pathfinder.py) 
- [VASP's guide for NEB](https://www.vasp.at/wiki/index.php/TS_search_using_the_NEB_Method)
- [Plug-in guide for CI-NEB](https://theory.cm.utexas.edu/vtsttools/neb.html)
