import logging
import re
from pathlib import Path

from ase.calculators.singlepoint import SinglePointCalculator
from clease import Evaluate, NewStructures
from clease.calculator import attach_calculator
from clease.montecarlo import Montecarlo
from clease.montecarlo.constraints import FixedElement
from clease.montecarlo.observers import EnergyEvolution, LowestEnergyStructure
from clease.settings import CECrystal, Concentration
from clease.tools import update_db as update_clease_db

from simmate.engine import Workflow
from simmate.file_converters.structure.ase import AseAtomsAdaptor
from simmate.toolkit import Structure
from simmate.utilities import get_chemical_subsystems, get_directory
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
        # distance between atoms in cluster in angstroms, number of values
        # increase w/ max cluster size
        cluster_diameter: list[int],  # ex: [7, 5, 5]
        space_group: int = 1,
        max_supercell_atoms: int = 64,
        current_generation: int = 0,  # or should this be inferred from the db?
        convergence_limit: float = 0.005,
        max_generations: int = 10,
        structures_per_generation: int = 10,
        # "relaxation.vasp.staged-cluster" --> Workflow below is for quick testing
        subworkflow_name: str = "static-energy.vasp.cluster-high-qe",
        subworkflow_kwargs: str = {},
        directory: Path = None,
        **kwargs,
    ):
        logging.critical(
            "This is a highly experimental (and largely incomplete) workflow. "
            "Proceed with caution and pay attention to the changelog for updates."
        )

        # ---------------------------------------------------------------------

        # SETUP

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
            basis=structure.frac_coords,
            db_name=str(directory / "clease_database.db"),
            max_cluster_dia=cluster_diameter,
        )

        # connect to the ASE database
        ase_database = settings.connect()
        # BUG: There might be issues if another calc is accessing the same
        # database or if a calc access the database of a previous run.
        # Consider making a unique database located in the working directory

        # ---------------------------------------------------------------------

        # LOAD OLD RESULTS

        # Load previously completed structures from the Simmate database and
        # add them to the ASE/Clease database
        # Following guide from...
        #   https://clease.readthedocs.io/en/stable/import_structures.html

        # TODO: consider filtering with concentration.todict() from source column
        # BUG: Will adding irrelevent compositions to the database break clease?
        # For now, I just filter any in the chemical system
        all_elements = list(set([e for es in basis_elements for e in es]))
        all_elements.sort()
        chemical_system = "-".join(all_elements)

        past_calculations = subworkflow.all_results.filter(
            chemical_system__in=get_chemical_subsystems(chemical_system),
            site_forces__isnull=False,
            energy__isnull=False,
        ).all()

        ns = NewStructures(settings)

        for past_calc in past_calculations:
            # convert from Database Structure --> Toolkit Structure --> ASE
            structure_result = past_calc.to_toolkit()
            atoms = AseAtomsAdaptor.get_atoms(structure_result)

            # set the results to the atoms object. We do this by creating
            # a basic calculator and attaching it
            calc = SinglePointCalculator(
                atoms=atoms,
                stress=past_calc.lattice_stress,
                forces=past_calc.site_forces,
                free_energy=past_calc.energy,
                energy=past_calc.energy,
            )
            atoms.set_calculator(calc)

            # documentation says we can just used the same structure for the
            # intitial/final if we'd like.
            try:
                ns.insert_structure(init_struct=atoms, final_struct=atoms)
            except Exception as error:
                logging.warning("Failed to load past structure due to:")
                logging.warning(error)

        # ---------------------------------------------------------------------

        # MAIN GENERATION LOOP

        # Start looping through CE generations
        for generation_number in range(current_generation, max_generations):
            logging.info(f"Starting Generation {generation_number}")

            # create a subdirectory to store results in
            generation_directory = get_directory(
                directory / f"generation_{generation_number}"
            )

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
                # convert the entry to an ASE atoms and then a Toolkit structure
                atoms = row.toatoms()
                structure_step = AseAtomsAdaptor.get_structure(atoms)

                # Submit a workflow for the new structure
                state = subworkflow.run_cloud(
                    structure=structure_step,
                    source={
                        "method": "clease+ase",
                        "id": row.id,
                        # TODO: consider storing concentration.todict()
                    },
                    **subworkflow_kwargs,
                )
                submitted_states.append(state)

            # Now iterate through our submitted calcs and save them to our
            # database as they finish
            for state in submitted_states:
                # wait for run to finish and load the results
                try:
                    result = state.result()  # structure_step
                except:
                    logging.warning("CALC {row.id} FAILED.")
                    continue
                # if isinstance(result, Exception):
                #     # TODO: do something with those that failed.
                #     continue

                # convert from Database Structure --> Toolkit Structure --> ASE
                structure_result = result.to_toolkit()
                atoms = AseAtomsAdaptor.get_atoms(structure_result)

                # set the results to the atoms object. We do this by creating
                # a basic calculator and attaching it
                calc = SinglePointCalculator(
                    atoms=atoms,
                    stress=result.lattice_stress,
                    forces=result.site_forces,
                    free_energy=result.energy,
                    energy=result.energy,
                )
                atoms.set_calculator(calc)

                # TODO: write pickle or JSON files for the result to the
                # generation_directory so that we can continue calcs

                # Load all results into the ase_database
                update_clease_db(
                    uid_initial=result.source["id"],
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
                fname=str(generation_directory / "CV.png"),
            )
            # set the alpha value with the one found above, and fit data using it.
            eva.set_fitting_scheme(fitting_scheme="l1", alpha=alpha)
            eva.fit()  # Run the fit with these settings.
            eva.plot_fit(
                interactive=False,
                savefig=True,
                fname=str(generation_directory / "Energies.png"),
            )
            # plot ECI values
            eva.plot_ECI(interactive=False)
            # save eci values into json
            eva.save_eci(
                fname=str(generation_directory / f"eci_gen_{generation_number}")
            )

            # check if the fit is converged
            if eva.rmse() <= convergence_limit and eva.loocv() <= convergence_limit:
                logging.info("CE model is converged. Exitting generation loop.")
                break

        # double check that the loop above exited thanks to convergence
        if eva.rmse() >= convergence_limit or eva.loocv() >= convergence_limit:
            logging.warning("Maximum generations hit before CE model converged.")

        # ---------------------------------------------------------------------

        # WRITE GROUND STATE

        # Once the loop exits above, we can write out ground state structures
        # https://clease.readthedocs.io/en/stable/aucu_probe_gs.html#generate-ground-state-structures

        # TODO

        # ---------------------------------------------------------------------

        # WORKUP + MONTE CARLO
        # TODO: This will likely move to a separate workflow

        # Likely inputs...
        #   chemical_system (composition range)
        #   max_atoms
        #   max supercell size
        #   temperature
        #   ECI / setttings from past runs
        #   elements to fix

        # BUG: many parameters assumed for early testing
        supercell_size = (3, 3, 3)
        temperature = 1e-10
        total_steps = 1000  # 10000000
        monitor_interval = 100

        # grab the ECI results (these are also stored in JSON files in the output)
        eci_results = eva.get_eci_dict()

        # use structure attached to the settings object as our starting point
        # and make it a supercell. Note it is an ASE atoms object
        supercell_to_test = settings.atoms.copy() * supercell_size
        # TODO: supercell size an input parameter

        # attach the CE model to it
        supercell_to_test = attach_calculator(
            settings,
            atoms=supercell_to_test,
            eci=eci_results,
        )

        # --- modify the input structure ---
        # TODO: Use the chemical_system parameter to generate all compositions
        # that should be evaluated. Then everything below will be in a for-loop
        # that runs a MC simulation on each (+ pulls the ground state structure)

        # randomly select sites and change composition via...
        # counter = 1234
        # while counter > 0:
        #     for i in range(len(atoms)):
        #         if atoms[i].symbol == 'Al':
        #             atoms[i].symbol = 'Sc'
        #             counter -= 1
        #             break

        # build simulation object
        monte_carlo_engine = Montecarlo(supercell_to_test, temperature)

        # set up constraints and input values
        constraint_01 = FixedElement("C")  # elements to fix and not move/update
        monte_carlo_engine.generator.add_constraint(constraint_01)
        # BUG: We assume only Carbon is constrained in early testing
        # BUG: clease docs indicate we likely need a ConstrainSwapByBasis

        # set up monitors to write output files during run
        observer_01 = EnergyEvolution(monte_carlo_engine)
        observer_02 = LowestEnergyStructure(supercell_to_test)

        monte_carlo_engine.attach(observer_01, monitor_interval)
        monte_carlo_engine.attach(observer_02, monitor_interval)

        # run the simulation
        monte_carlo_engine.run(steps=total_steps)

        # write output files
        thermo = monte_carlo_engine.get_thermodynamic_quantities()
        # TODO: this is a dictionary of data that I can hold on to for EACH
        # composition + MC run. Then I'd put all results together in a
        # pandas dataframe and write to a CSV. Maybe write a new CSV each cycle
        # too.

        # TODO: write summary files using our observers
        # energy_progression = observer_01.energies
        # structure_best = observer_02.atoms

        # TODO: generate and plot the hull diagram using pymatgen
