# Nudged Elastic Band (NEB)

NEB is a technique used to determine the energy barrier of a specific migration pathway, such as atomic diffusion.

## Components of Nudged Elastic Band

** Note: Steps 3-5 are executed for each individual pathway **

1. Relax the initial bulk structure

2. Identify all symmetrically unique pathways

3. Relax the start/end supercell images 
    (or only one if they are equivalent)

4. Interpolate the start/end supercell images and relax these
    using IDPP.

5. Relax all images using NEB


## Potential Inputs

Depending on the workflow, a user may wish to begin at a different step. For instance, they might have a specific start/end structure they want to use instead of automatically detecting unique pathways. Hence, we divide this workflow into several smaller ones. We need to consider the following input scenarios:

1. `all_paths`: A bulk crystal and diffusing species are provided, and a full analysis of all paths is requested.

2. `single_path`: A bulk crystal, diffusing species, and pathway index are provided. The index specifies the particular pathway to be extracted from DistinctPathFinder. For instance, if DistinctPathFinder finds 5 unique paths, you can specify "I want to run the 4th pathway in this list (i.e., the 4th shortest pathway)."

3. `from_startend_sites`: A bulk crystal and start/end sites for the diffusing ion are provided, and that specific pathway should be analyzed. This would allow for a diffusion pathway that goes from a site at (0,0,0) to (1,1,1), for example.

4. `from_endpoints`: Two endpoint supercell structures are provided, and the specific pathway (from interpolated structures) should be analyzed.

5. `from_images`: A series of images are provided and analyzed.

In addition to these five scenarios, we also consider...

- Vacancy vs. interstitial diffusion
- Plugins for CI-NEB (currently not implemented)


## Useful Links

- [Atomate NEB yaml](https://github.com/hackingmaterials/atomate/blob/main/atomate/vasp/workflows/base/library/neb.yaml)
- [Atomate NEB py](https://github.com/hackingmaterials/atomate/blob/b9ad04e3ae892c51ba2e4d5c045db1c563f287f4/atomate/vasp/workflows/base/neb.py#L10)
- [pymatgen-diffusion neb](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/io.py)
- [pymatgen-diffusion pathfinder](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/pathfinder.py) 
- [VASP's guide for NEB](https://www.vasp.at/wiki/index.php/TS_search_using_the_NEB_Method)
- [Plug-in guide for CI-NEB](https://theory.cm.utexas.edu/vtsttools/neb.html)