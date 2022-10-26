import logging
import re
from pathlib import Path

from ase.calculators.singlepoint import SinglePointCalculator
from clease import Evaluate, NewStructures
from clease.settings import CECrystal, Concentration
from clease.tools import update_db as update_clease_db

from simmate.file_converters.structure.ase import AseAtomsAdaptor
from simmate.toolkit import Structure
from simmate.utilities import get_directory
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
        # distance between atoms in cluster in angstroms, number of values
        # increase w/ max cluster size
        cluster_diameter: list[int],  # ex: [7, 5, 5]
        space_group: int = 1,
        max_supercell_atoms: int = 64,
        current_generation: int = 0,  # or should this be inferred from the db?
        max_generations: int = 10,
        structures_per_generation: int = 10,
        # "relaxation.vasp.staged-cluster" --> Workflow below is for quick testing
        subworkflow_name: str = "static-energy.vasp.cluster-high-qe",
        subworkflow_kwargs: str = {},
        directory: Path = None,
        **kwargs,
    ):

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

        # TODO:
        # Load previously completed structures from the Simmate database and
        # add them to the ASE/Clease database

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

    # TODO:
    # Once the loop exits above, we can write out ground state structures
    # https://clease.readthedocs.io/en/stable/aucu_probe_gs.html#generate-ground-state-structures

    # THE CODE BELOW IS FROM LAURENS NOTES -- WHICH STILL NEED REFACTORED
    # AND INTEGRATED
    # these are taken from calculations
    # eci = {
    #   "c0": -6.752985422516767,
    #   "c1_0": 1.3253551890476376,
    #   "c2_d0004_0_00": 0.05988049764247872,
    #   "c2_d0006_0_00": -0.0018572335717313064,
    #   "c2_d0012_0_00": 0.014205248021860049,
    #   "c2_d0015_0_00": 0.0031493348052340623,
    #   "c3_d0014_0_000": 0.05990599094884079,
    #   "c3_d0015_0_000": 0.09078354301781237,
    #   "c3_d0016_0_000": -0.01761712377073125,
    #   "c3_d0017_0_000": -0.0003400461721735883,
    #   "c3_d0022_0_000": -0.052801823384517076,
    #   "c3_d0025_0_000": 0.12194678755743693,
    #   "c3_d0027_0_000": -0.15850374460679964,
    #   "c3_d0040_0_000": 0.02892551579759695,
    #   "c4_d0001_0_0000": 0.057727129322994564,
    #   "c4_d0002_0_0000": -0.07458756016332646,
    #   "c4_d0003_0_0000": 0.09689600405458178,
    #   "c4_d0004_1_0000": 0.023964593114969332
    # }

    # from clease.calculator import attach_calculator
    # atoms = settings.atoms.copy()*(3, 3, 3)
    # atoms = attach_calculator(settings, atoms=atoms, eci=eci)
    # print(atoms)

    # def Al2Sc(a):
    #     counter = a
    #     while counter > 0:
    #         for i in range(len(atoms)):
    #             if atoms[i].symbol == 'Al':
    #                 atoms[i].symbol = 'Sc'
    #                 counter -= 1
    #                 break
    #     print(atoms)

    # def Sc2Al(a):
    #     counter = a
    #     while counter > 0:
    #         for i in range(len(atoms)):
    #             if atoms[i].symbol == 'Sc':
    #                 atoms[i].symbol = 'Al'
    #                 counter -= 1
    #                 break
    #     print(atoms)

    # def runmc(frac):
    #     from clease.montecarlo import Montecarlo
    #     from clease.montecarlo.constraints import FixedElement
    #     from clease.montecarlo.observers import EnergyEvolution
    #     from clease.montecarlo.observers import LowestEnergyStructure
    #     cnst = FixedElement('C')
    #     T = 1e-10
    #     counter = 1
    #     while counter < 2:
    #         counter = counter + 1
    #         Al2Sc(frac)
    #         mc = Montecarlo(atoms, T)
    #         obs = EnergyEvolution(mc)
    #         obs2 = LowestEnergyStructure(atoms)
    #         mc.attach(obs, interval=100)
    #         mc.attach(obs2, interval=1000)
    #         mc.generator.add_constraint(cnst)
    #         mc.run(steps=10000000)
    #         thermo = mc.get_thermodynamic_quantities()
    #         les = obs2.atoms
    #         with open('thermo_AlScC_0K.csv', 'a', newline='') as f:
    #              writer = csv.writer(f)
    #              writer.writerow([thermo.get('energy'), thermo.get('F_conc')])

    # # run:
    # count = 1296 #change this to the number of atoms you want to change
    # i = 1 #change this to step value
    # while i < count:
    #     runmc(1)
    #     i += 1
