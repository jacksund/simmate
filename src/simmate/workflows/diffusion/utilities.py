# -*- coding: utf-8 -*-

from pymatgen.core.sites import PeriodicSite
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder, MigrationPath


# --------------------------------------------------------------------------------------


def get_oxi_supercell_path(path, min_sl_v=None, oxi=False):

    if oxi:
        # add oxidation states to structure
        structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure
    else:
        structure = path.symm_structure

    structure_supercell = structure.copy()
    if min_sl_v:
        structure_supercell = structure.copy()
        supercell_size = [
            (min_sl_v // length) + 1 for length in structure_supercell.lattice.lengths
        ]
        structure_supercell.make_supercell(supercell_size)

    isite_new = PeriodicSite(
        species=structure[path.iindex].specie,  # make sure to grab new oxi state
        coords=path.isite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )
    esite_new = PeriodicSite(
        species=structure[path.eindex].specie,  # make sure to grab new oxi state
        coords=path.esite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )

    path_new = MigrationPath(isite_new, esite_new, structure_supercell)
    # BUG: the init script for MigrationPath can't identify the site indexes properly
    # but they should be the same as before because it is a symmetrized structure. Note
    # that even if I'm wrong in some case -- this will have no effect because iindex
    # and eindex are only used in one portion of the hash as well as for printing
    # the __str__ of the object.
    path_new.iindex = path.iindex
    path_new.eindex = path.eindex

    return path_new


def get_oxi_supercell_path_OLD(structure, path, min_sl_v):

    # if desired, add oxidation states to structure
    structure = ValenceIonicRadiusEvaluator(structure).structure

    # make the supercell
    supercell = structure.copy()
    supercell_size = [(min_sl_v // length) + 1 for length in supercell.lattice.lengths]
    supercell.make_supercell(supercell_size)

    # run the pathway analysis using the supercell structure
    dpf = DistinctPathFinder(
        structure=supercell,
        migrating_specie="F-",
        max_path_length=path.length + 1e-5,  # add extra for rounding errors
        symprec=0.1,
        perc_mode=None,
    )

    # go through paths until we find a match
    # assume we didn't find a match until proven otherwise
    found_match = False
    for path_check in dpf.get_paths():
        if (
            abs(path.length - path_check.length) <= 1e-5  # capture rounding error
            and path.iindex == path_check.iindex
            and path.eindex == path_check.eindex
        ):
            # we found a match so break. No need to check any other pathways.
            found_match = True
            break

    # Just in case we didn't find a match, we need to raise an error
    if not found_match:
        raise Exception("Failed to find the equivalent pathway in the supercell")

    # we now have path_check as the equivalent pathway. This is what the user
    # wants so we can return it
    return path_check


# --------------------------------------------------------------------------------------
