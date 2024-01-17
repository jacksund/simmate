# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.apps.bader.workflows import PopulationAnalysis__Bader__Badelf
from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.database.third_parties import MatprojStructure
from simmate.engine import Workflow
from simmate.toolkit import Structure
from simmate.utilities import copy_files_from_directory


class PopulationAnalysis__VaspBader__BadelfMatproj(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning.
    """

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        empty_sites: list[float] = [],
        empty_ion: str = None,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        if empty_sites and empty_ion:
            raise Exception(
                "You can only specify either empty_sites or an empty_ion type. "
                "Not both."
            )

        if empty_ion:
            # Check if the input structure given already has the empty atom in
            # it. If so, we need to delete the empty atoms to get the base structure
            if empty_ion in [e.symbol for e in structure.composition.elements]:
                structure_w_empties = structure.copy()
                structure.remove_species(empty_ion)
            # Otherwise we run database queries to find a potential match
            else:
                # load the structure that contains dummy atoms in it
                structure_w_empties = get_structure_w_empties(
                    structure=structure,
                    empty_ion=empty_ion,
                )

        elif empty_sites:
            # Select an empty element that is NOT already in the structure
            for empty_ion in ["H", "He", "Lv"]:
                if empty_ion not in [e.symbol for e in structure.composition.elements]:
                    break
            structure_w_empties = structure.copy()
            for empty_coords in empty_sites:
                structure_w_empties.append(
                    species=empty_ion,
                    coords=empty_coords,  # I assume fractional coords
                )

        else:
            # otherwise no empties will be used
            # Still, select an empty element that is NOT already in the structure
            empty_ion = None
            structure_w_empties = structure.copy()

        # Run the pre-static energy calculation to generate our CHGCAR and ELFCAR
        prebadelf_dir = directory / StaticEnergy__Vasp__PrebadelfMatproj.name_full
        StaticEnergy__Vasp__PrebadelfMatproj.run(
            structure=structure,
            command=command,
            source=source,
            directory=prebadelf_dir,
        ).result()

        # And run the bader analysis on the resulting chg denisty + elfcar
        badelf_dir = directory / PopulationAnalysis__Bader__Badelf.name_full
        PopulationAnalysis__Bader__Badelf.run(
            structure=structure_w_empties,
            directory=badelf_dir,
            previous_directory=prebadelf_dir,
        ).result()

        # The from_vasp_directory method that loads results into the database
        # requires the following files to be in the main directory:
        #  1. the ACF.dat
        #  2. INCAR
        #  3. vasprun.xml
        #  4. POTCAR
        #  5. CHGCAR_empty
        copy_files_from_directory(
            files_to_copy=["ACF.dat", "CHGCAR_empty"],
            directory_new=directory,
            directory_old=badelf_dir,
        )
        copy_files_from_directory(
            files_to_copy=["INCAR", "vasprun.xml", "POTCAR"],
            directory_new=directory,
            directory_old=prebadelf_dir,
        )
        # !!! I need a better way to access these files in the workup method
        # without copying them into the main dir...


# -----------------------------------------------------------------------------

# Below are extra tasks and subflows for the workflow that is defined above


class StaticEnergy__Vasp__PrebadelfMatproj(StaticEnergy__Vasp__Matproj):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    _incar_updates = dict(
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. useds NGX instead of NGXF)
        NGX__density_a=10,
        NGY__density_b=10,
        NGZ__density_c=10,
    )


def get_structure_w_empties(structure, empty_ion):
    """
    Searches the Materials Project database for a structure that contains
    the extra ion and matching host lattice, and uses it to introduce
    empty atoms into the original structure. For example, if your input
    gave a Ca2N structure and Cl ion for the template, this function will
    find Ca2NCl in the Matproj database and then use the Cl sites to
    add dummy "H" atoms into the Ca2N structure. This is particularly useful
    if you would like to analyze electrides.
    """

    # !!! It might make more sense to have this accept a database Structure object
    # and also search the same table for a match (rather than the Matproj).

    # Grab the chemical system of the structure when it includes the empty ion
    structure_dummy = structure.copy()
    # coords don't matter here bc I'm just after the chemical_system
    structure_dummy.append(empty_ion, [0, 0, 0])
    template_system = structure_dummy.composition.chemical_system

    # Go through the Materials Project database and find a structure that
    # is matching when the empty ion type is ignored.
    matcher = StructureMatcher(
        ignored_species=empty_ion,
        primitive_cell=False,  # required for the get_s2_like_s1 method
    )
    potential_matches = MatprojStructure.objects.filter(
        chemical_system=template_system
    ).all()
    for potential_match in potential_matches:
        structure_template = potential_match.to_toolkit()
        is_match = matcher.fit(structure, structure_template)
        # Once we find a match, stop searching
        if is_match:
            break

    # confirm that we successfully found a match
    if not is_match:
        raise Exception("No match found when trying to generate empty sites")

    # convert our match to an equivalent basis set as the original input
    # structure -- this ensures frac coords are matches.
    structure_template = matcher.get_s2_like_s1(structure, structure_template)

    # make a copy because we will be modifying the structure
    structure_w_empties = structure.copy()
    for site in structure_template.sites:
        if site.specie.symbol == empty_ion:
            structure_w_empties.append(empty_ion, site.frac_coords)

    # TODO: consider doing a check to ensure the empty atoms added are reasonable.
    # A simple check could be to use the SiteDistance validator and make sure
    # the hydrogen isn't too close to another atom.

    # write the new structure to file
    # filename = directory / "simmate_structure_w_empties.cif"
    # structure_w_empties.to(filename=str(filename), fmt="cif")

    return structure_w_empties
