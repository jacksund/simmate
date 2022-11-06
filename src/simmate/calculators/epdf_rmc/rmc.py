# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from random import random

import matplotlib.pyplot as plt
import numpy

import simmate.toolkit.transformations.from_ase as ase_transform_module
from simmate.calculators.epdf_rmc.slab import RdfSlab
from simmate.toolkit import Structure
from simmate.toolkit import transformations as transform_mod
from simmate.toolkit.validators import structure as validator_mod
from simmate.workflow_engine import Workflow


class EpdfRmc__Toolkit__FitExperimental(Workflow):

    use_database = False

    @staticmethod
    def run_config(
        structure: Structure,
        experimental_G_csv: str,
        prdf_kwargs: dict = {"bin_size": 0.04},
        error_constant: float = 5e-7,
        max_steps: int = 1000,
        transformations: dict = {
            "from_ase.CoordinatePerturbation": {
                "perturb_strength": 0.005,
                "ratio_of_covalent_radii": 0.1,
            },
            # "AtomHop": {},
        },
        validators: dict = {
            "SiteDistance": {"distance_cutoff": 1.2},
            # "SlabThickness": {"max_thickness": 15.71},
            # "TargetDensity": {"target_density": 2.38},
            # "DistancesCoordination": {
            #     "MinBondLength": {
            #         ("Al", "Al"): 1.8,
            #         ("Al", "O"): 1.2,
            #         ("O", "O"): 1.8,
            #     },
            #     "CoordinationRange": {"Al": [2, 7], "O": [1, 4]},
            # },
        },
        directory: Path = None,
        **kwargs,
    ):

        # convert from a Structure to SlabStructure object
        initial_structure = RdfSlab.from_dict(structure.as_dict())

        # convert validators + transformations all to proper python class
        # below is an example loop with transformations
        transformation_objects = []
        for t_name, t_kwargs in transformations.items():
            if t_name.startswith("from_ase."):
                # all start with "from_ase" so I assume that import for now
                ase_class_str = t_name.split(".")[-1]
                transformation_class = getattr(ase_transform_module, ase_class_str)
                # transformer = transformation_class(**t_kwargs)
            elif hasattr(transform_mod, t_name):
                transformation_class = getattr(transform_mod, t_name)
                # transformer = t_class(**t_kwargs)
            else:
                raise Exception(f"Unknown validator provided ({t_name})")
            transformation_objects.append(transformation_class)

        # dynamically build our validator objects
        validator_objects = []
        for v_name, v_kwargs in validators.items():
            if hasattr(validator_mod, v_name):
                v_class = getattr(validator_mod, v_name)
                v_obj = v_class(**v_kwargs)
            else:
                raise Exception(f"Unknown validator provided ({v_name})")
            validator_objects.append(v_obj)

        # check that the input structure is valid
        for validator in validator_objects:
            if not validator.check_structure(initial_structure):
                raise Exception(
                    "Input structure does not meet the constraints set by your "
                    "validators. Please fix your structure or adjust constraints. "
                    f"The first check to fail was {validator.name}"
                )

        # Make a copy of the input structure because we will be manipulating it
        current_structure = initial_structure.copy()

        # load experimental G(r)
        current_structure.load_experimental_from_file(experimental_G_csv)

        # PLOT FOR DEBUGGING
        plt.plot(current_structure.G_experimental)
        plt.show()
        plt.plot(current_structure.full_pdf_G)
        plt.show()

        # Build out initial values and then start the RMC loop
        current_error = current_structure.prdf_error
        nsteps = 0
        c_error = "{:.5E}".format(current_error)
        logging.info(f"Initial Structure. Error = '{c_error}'.")
        successful_steps = []
        error_list = []
        while nsteps < max_steps:
            nsteps += 1

            # TODO: add logic to select a transformation
            # TODO: apply with validation
            # for now, just grab the first transformation
            transformer = transformation_objects[0]

            trial_structure = current_structure.copy()

            # TODO: need a better way of passing kwargs
            new_structure = transformer.apply_transformation(
                trial_structure,
                **transformations[transformer.name],  # gives the kwargs dict
            )

            is_valid = True  # true until proven otherwise
            for validator in validator_objects:
                if not validator.check_structure(new_structure):
                    is_valid = False
                    break  # one failure is enough to stop and reject the structure
            if not is_valid:
                logging.info(f"Step {nsteps}. Move not valid.")
                continue  # restart the while loop

            # BUG-FIX: transformations convert back to structure objects, which
            # loses everything attached to the SlabStructure object. We need
            # to rebuild it here.
            new_structure = RdfSlab.from_dict(new_structure.as_dict())
            new_structure.load_experimental_from_file(experimental_G_csv)

            new_error = new_structure.prdf_error
            new_e = "{:.5E}".format(new_error)

            keep_new = True
            if new_error < current_error:
                # accept new structure
                keep_new = True
                logging.info(f"Step {nsteps}. Error improved, error = '{new_e}'.")
            else:
                # accept new structure with some probability or just restart the loop
                probability = numpy.exp(
                    -1 * (abs(new_error - current_error)) / error_constant
                )
                if random() < probability:
                    keep_new = True
                    logging.info(
                        f"Step {nsteps}. Error is worse but accepting move, "
                        f"error = '{new_e}'."
                    )
                else:
                    keep_new = False
                    logging.info(f"Step {nsteps}. Error is worse, rejecting move.")

            if keep_new:
                current_structure = new_structure
                current_error = new_error
                error_list.append(new_error)
                successful_steps.append(nsteps)
                current_structure.to("cif", directory / f"structure_step_{nsteps}.cif")

                plt.plot(current_structure.full_pdf_G)
                plt.show()

        output_structure = current_structure
        output_structure.to("cif", directory / "final_rmc_structure.cif")
        logging.info(f"successful_steps = {successful_steps}")
        return output_structure


# ---- DASK LOOP NOTES ----
# from dask.distributed import Client
# client = Client()
# failed_cycles = 0
# new_structure = False
# while not new_structure:
#     futures = [
#         client.submit(
#             make_candidate_structure,
#             current_structure,
#             validator_objects,
#             transformer,
#             pure=False,
#         )
#         for n in range(1000)
#     ]
#     for future in futures:
#         new_structure = future.result()
#         if new_structure:
#             break
#     for future in futures:
#         future.cancel()
#     if not new_structure:
#         print(
#             "Failed to find valid structure with 1000 attempts. Trying again."
#         )
#         failed_cycles += 1
#         if failed_cycles >= 10:
#             print("Critical failure. Returning most recent structure")
#             return current_structure
# def make_candidate_structure(
#     current_structure, validator_objects, transformer
# ):
#     new_structure = transformer.apply_transformation(current_structure)
#     is_valid = True  # true until proven otherwise
#     for validator in validator_objects:
#         if not validator.check_structure(new_structure):
#             is_valid = False
#             break  # one failure is enough to stop and reject the structure
#     if not is_valid:
#         return False
#     return new_structure
