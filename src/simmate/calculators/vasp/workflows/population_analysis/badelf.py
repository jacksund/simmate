# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.calculators.bader.workflows import PopulationAnalysis__Bader__Badelf
from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.database.third_parties import MatprojStructure
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


class PopulationAnalysis__Vasp__BadelfMatproj(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning.
    """

    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):

        prebadelf_result = PopulationAnalysis__Vasp__PrebadelfMatproj.run(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
        ).result()

        # load the structure that contains dummy atoms in it
        structure_w_empties = get_structure_w_empties(
            structure=structure,
            empty_ion_template="F",
        )

        # Bader only adds files and doesn't overwrite any, so I just run it
        # in the original directory. I may switch to copying over to a new
        # directory in the future though.
        badelf_result = PopulationAnalysis__Bader__Badelf.run(
            structure=structure_w_empties,
            directory=prebadelf_result["directory"],
        ).result()

        save_badelf_results(badelf_result, prebadelf_result["run_id"])


# -----------------------------------------------------------------------------

# Below are extra tasks and subflows for the workflow that is defined above


class PopulationAnalysis__Vasp__PrebadelfMatproj(StaticEnergy__Vasp__Matproj):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = StaticEnergy__Vasp__Matproj.incar.copy()
    incar.update(
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. useds NGX instead of NGXF)
        NGX__density_a=12,
        NGY__density_b=12,
        NGZ__density_c=12,
    )


def get_structure_w_empties(
    structure,
    empty_ion_template,
    # directory,
):
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

    # Grab the chemical system of the structure when it includes the empty ion template
    structure = Structure.from_dynamic(
        structure
    )  # !!! because we don't load input in this flow yet
    structure_dummy = structure.copy()
    structure_dummy.append(
        empty_ion_template, [0, 0, 0]
    )  # coords don't matter here bc I'm just after the chemical_system
    template_system = structure_dummy.composition.chemical_system

    # Go through the Materials Project database and find a structure that
    # is matching when the empty ion type is ignored.
    matcher = StructureMatcher(
        ignored_species=empty_ion_template,
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
        if site.specie.symbol == empty_ion_template:
            structure_w_empties.append("H", site.frac_coords)

    # TODO: consider doing a check to ensure the H atoms added are reasonable.
    # A simple check could be to use the SiteDistance validator and make sure
    # the hydrogen isn't too close to another atom.

    # write the new structure to file
    # filename = directory / "simmate_structure_w_empties.cif"
    # structure_w_empties.to("cif", filename)

    return structure_w_empties


# THIS IS A COPY/PASTE FROM THE BADER WORKFLOW -- I need to condense these
def save_badelf_results(bader_result, run_id):
    # load the results. We are particullary after the first result with
    # is a pandas dataframe of oxidation states.
    oxidation_data, extra_data = bader_result["result"]

    # load the calculation entry for this workflow run. This should already
    # exist thanks to the load_input_and_register task of the prebader workflow
    calculation = PopulationAnalysis__Bader__Badelf.database_table.from_run_context(
        run_id,
        PopulationAnalysis__Vasp__PrebadelfMatproj.name_full,
    )
    # BUG: can't use context to grab the id because workflow tasks generate a
    # different id than the main workflow

    # now update the calculation entry with our results
    calculation.oxidation_states = list(oxidation_data.oxidation_state.values)
    calculation.save()
