# -*- coding: utf-8 -*-

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.workflow_engine import (
    s3task_to_workflow,
    task,
    Parameter,
    Workflow,
    ModuleStorage,
)
from simmate.database import connect
from simmate.database.third_parties import MatProjStructure
from simmate.calculators.vasp.tasks.population_analysis import (
    MatProjPreBaderELF,
)
from simmate.calculators.bader.tasks import BaderELFAnalysis
from simmate.calculators.vasp.database.population_analysis import (
    MatProjBaderELFAnalysis as MPBadelfResults,
)

prebadelf_matproj_workflow = s3task_to_workflow(
    name="population-analysis/prebadelf-matproj",
    module=__name__,
    project_name="Simmate-PopulationAnalysis",
    s3task=MatProjPreBaderELF,
    calculation_table=MPBadelfResults,
    register_kwargs=["structure", "source"],
    description_doc_short="runs Bader analysis with ELFCAR as reference",
)

prebadelf_task = prebadelf_matproj_workflow.to_workflow_task()

badelf_task = BaderELFAnalysis()


@task
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
    find Ca2NCl in the MatProj database and then use the Cl sites to
    add dummy "H" atoms into the Ca2N structure. This is particularly useful
    if you would like to analyze electrides.
    """

    # !!! It might make more sense to have this accept a database Structure object
    # and also search the same table for a match (rather than the MatProj).

    # Grab the chemical system of the structure when it includes the empty ion template
    structure_dummy = structure.copy()
    structure_dummy.append(
        empty_ion_template, [0, 0, 0]
    )  # coords don't matter here bc I'm just after the chemical_system
    template_system = structure_dummy.composition.chemical_system

    # Go through the Materials Project database and find a structure that
    # is matching when the empty ion type is ignored.
    matcher = StructureMatcher(ignored_species=empty_ion_template)
    potential_matches = MatProjStructure.objects.filter(
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

    # make a copy because we will be modifying the structure
    structure_w_empties = structure.copy()

    for site in structure_template.sites:
        if site.specie.symbol == empty_ion_template:
            structure_w_empties.append("H", site.frac_coords)

    # write the new structure to file
    # filename = os.path.join(directory, "simmate_structure_w_empties.cif")
    # structure_w_empties.to("cif", filename)

    return structure_w_empties


# THIS IS A COPY/PASTE FROM THE BADER WORKFLOW -- I need to condense these
@task
def save_bader_results(bader_result, prefect_flow_run_id):
    # load the results. We are particullary after the first result with
    # is a pandas dataframe of oxidation states.
    oxidation_data, extra_data = bader_result["result"]

    # load the calculation entry for this workflow run. This should already
    # exist thanks to the load_input_and_register task of the prebader workflow
    calculation = MPBadelfResults.from_prefect_id(
        prefect_flow_run_id,
    )
    # BUG: can't use context to grab the id because workflow tasks generate a
    # different id than the main workflow

    # now update the calculation entry with our results
    calculation.oxidation_states = list(oxidation_data.oxidation_state.values)
    calculation.save()


with Workflow("population-analysis/badelf-matproj") as workflow:

    structure = Parameter("structure")
    command = Parameter("command", default="vasp_std > vasp.out")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)

    prebadelf_result = prebadelf_task(
        structure=structure,
        command=command,
        source=source,
        directory=directory,
    )

    # load the structure that contains dummy atoms in it
    structure_w_empties = get_structure_w_empties(
        structure=structure,
        empty_ion_template="F",
    )

    # Bader only adds files and doesn't overwrite any, so I just run it
    # in the original directory. I may switch to copying over to a new
    # directory in the future though.
    badelf_result = badelf_task(
        structure=structure_w_empties,
        directory=prebadelf_result["directory"],
    )

    save_bader_results(badelf_result, prebadelf_result["prefect_flow_run_id"])


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-PopulationAnalysis"
workflow.calculation_table = MPBadelfResults
workflow.result_table = MPBadelfResults
workflow.register_kwargs = ["structure", "source"]
workflow.result_task = prebadelf_result
workflow.s3tasks = [MatProjPreBaderELF, BaderELFAnalysis]

workflow.__doc__ = """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning.
"""
