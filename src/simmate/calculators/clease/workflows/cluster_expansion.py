import logging
import re
from pathlib import Path

from clease import Evaluate, NewStructures
from clease.settings import CECrystal, Concentration
from clease.tools import update_db as update_clease_db

from simmate.file_converters.structure.ase import AseAtomsAdaptor
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow


class ClusterExpansion__Clease__BulkStructure(Workflow):
    use_database = False

    @staticmethod
    def run_config(
        # template structure loaded from file
        structure: Structure,
        # to vary some elements in your CE, use the format <y-x>X<x> and define
        # your x as the threshold of variance
        # for ex. in this we have "C<1>" because we want the concentration to
        # remain constant and we have Al/Sc<1-x>X<x> because we want there to
        # be maximum 2 atoms of one or the other to 1 carbon atom
        formula_unit: list[str],  # ex: ["Al<x>Sc<1-x>", "C<1>"]
        variable_range: dict,  # ex: {"x": (0, 1), "y": (0, 1)}
        db_name: str = "database.db",
        space_group: int = 1,
        max_supercell_atoms: int = 64,
        # distance between atoms in cluster in angstroms, number of values
        # increase w/ max cluster size
        cluster_diameter: list[int] = [7, 5, 5],  # should this be required?
        current_generation: int = 0,  # or should this be inferred from the db?
        max_generations: int = 10,
        structures_per_generation: int = 10,
        subworkflow_name: str = "relaxation.vasp.staged-cluster",
        subworkflow_kwargs: str = {},
        directory: Path = None,
        **kwargs,
    ):
        breakpoint()

        # load the workflow that we want to do individual relaxations with
        subworkflow = get_workflow(subworkflow_name)

        # Grab the list of elements from each formula unit. For example,
        # ["Al<x>Sc<1-x>", "C<1>", "Sc<y>Al<1-y>"] would give...
        # [["Al", "Sc"], ["C"], ["Sc", "Al"]],
        basis_elements = [re.split("<.*?>", f)[:-1] for f in formula_unit]

        # define concentration
        concentration = Concentration(basis_elements=basis_elements)
        concentration.set_conc_formula_unit(
            formula_unit,
            variable_range=variable_range,
        )

        # Build out the cluster expansion settings
        settings = CECrystal(
            concentration=concentration,
            spacegroup=space_group,
            # data from lattice definition
            cellpar=structure.lattice.parameters,  # [a, b, c, alph, beta, gamma]
            supercell_factor=max_supercell_atoms,
            basis=structure.cart_coords,
            db_name=db_name,
            max_cluster_dia=cluster_diameter,
        )

        # connect to the ASE database
        ase_database = settings.connect()
        # BUG: There might be issues if another calc is accessing the same
        # database or if a calc access the database of a previous run.
        # Consider making a unique database located in the working directory

        # TODO:
        # Load previously completed structures from the Simmate database and
        # add them to the ASE/Clease database

        # Start looping through CE generations
        for generation_number in range(current_generation, max_generations):
            logging.info(f"Starting Generation {generation_number}")

            # create new structures based on the generation we are on
            ns = NewStructures(
                settings,
                generation_number=generation_number,
                struct_per_gen=structures_per_generation,
            )
            if generation_number == 0:
                ns.generate_initial_pool()
            else:
                ns.generate_probe_structure()

            # grab all structures in the database that have haven't converged
            # (i.e. all the new ones).
            # BUG: how are failed calculations handled?
            submitted_states = []
            for row in ase_database.select(converged=False):
                pass
                # convert the entry to an ASE atoms and then a Toolkit structure
                atoms = row.toatoms()
                structure_step = AseAtomsAdaptor.get_structure(atoms)

                # Submit a workflow for the new structure
                state = subworkflow.run_cloud(
                    structure=structure_step,
                    source={
                        "method": "clease+ase",
                        "id": row.id,
                    },
                    **subworkflow_kwargs,
                )
                submitted_states.append(state)

            # Now iterate through our submitted calcs and save them to our
            # database as they finish
            for state in submitted_states:
                # wait for run to finish and load the results
                result = state.result()

                # convert from Database Structure --> Toolkit Structure --> ASE
                structure_result = result.to_toolkit()
                atoms = AseAtomsAdaptor.get_atoms(structure_result)

                # Load all results into the ase_database
                update_clease_db(
                    uid_initial=result.source.id,
                    final_struct=atoms,
                    db_name=settings.db_name,
                )
                # BUG: How do we set the energy to the atoms object?
                # custom_kvp_final or maybe overwrite get_potential_energy...?

            # Now that all results are in the database, run an evaluation to
            # check how things are going.
            eva = Evaluate(settings=settings, scoring_scheme="loocv")
            # scan different values of alpha and return the value of alpha that yields
            # the lowest CV score
            # alpha is the regularization parameter designed to penalize model complexity
            # higher the alpha, less complex model, decreasing error due to variance
            # alphas that are too high increase error due to bias (underfit)
            eva.set_fitting_scheme(fitting_scheme="l1")
            alpha = eva.plot_CV(
                alpha_min=1e-7,
                alpha_max=1.0,
                num_alpha=50,
                savefig=True,
                fname=str(directory / "CV.png"),
            )
            # set the alpha value with the one found above, and fit data using it.
            eva.set_fitting_scheme(fitting_scheme="l1", alpha=alpha)
            eva.plot_fit(
                interactive=False,
                savefig=True,
                fname=str(directory / "Energies.png"),
            )
            # plot ECI values
            eva.plot_ECI()
            # save eci values into json
            eva.save_eci(fname=str(directory / "eci_H1_l1"))

    # TODO:
    # Once the loop exits above, we can write out ground state structures
    # https://clease.readthedocs.io/en/stable/aucu_probe_gs.html#generate-ground-state-structures
