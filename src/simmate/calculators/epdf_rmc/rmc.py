# -*- coding: utf-8 -*-

from random import random

from numpy import exp

from simmate.calculators.epdf_rmc.slab import RdfSlab
from simmate.toolkit import transformations as transform_mod
from simmate.toolkit import validators as validator_mod

error_list = []


def run_rmc(
    initial_structure="CONTCAR",
    experimental_G_csv="ED5_DF_gr_tabbed.gr",
    prdf_args={"bin_size": 0.04},
    error_constant=5e-7,
    transformations={
        "AtomHop": {},  # consider adding a second, smaller step size "max_step": 0.2
    },
    validators={
        "SlabThickness": {"max_thickness": 15.71},
        "TargetDensity": {"target_density": 2.38},
        "DistancesCoordination": {
            "MinBondLength": {
                ("Al", "Al"): 1.8,
                ("Al", "O"): 1.2,
                ("O", "O"): 1.8,
            },
            "CoordinationRange": {"Al": [2, 7], "O": [1, 4]},
        },
    },
    max_steps=1000,
):

    # convert to our python class
    initial_structure = RdfSlab.from_file(initial_structure)

    initial_structure.xyz_df = xyz(initial_structure)

    # load experimental G(r)
    initial_structure.load_experimental_from_file(experimental_G_csv)

    # convert validators + transformations all to proper python class
    # below is an example loop with transformations
    transformation_objects = []
    for t_name, t_kwargs in transformations.items():
        t_class = getattr(transform_mod, t_name)
        t_obj = t_class(**t_kwargs)
        transformation_objects.append(t_obj)

    # dynamically build our validator objects
    validator_objects = []
    for v_name, v_kwargs in validators.items():
        if v_name == "SlabThickness":
            v_obj = SlabThickness(**v_kwargs)
        elif v_name == "TargetDensity":
            v_obj = TargetDensity(**v_kwargs)
        elif v_name == "DistancesCoordination":
            v_obj = DistancesCoordination(**v_kwargs)
        else:
            v_class = getattr(validator_mod, v_name)
            v_obj = v_class(**v_kwargs)
        validator_objects.append(v_obj)

    # check that the input structure is valid
    """
    for validator in validator_objects:
        if not validator.check_structure(initial_structure):
            print(validator)
            raise Exception(
                "Input structure does not meet the constraints set by your "
                "validators. Please fix your structure or adjust constraints."
            )
    """
    # Start the RMC loop
    current_structure = initial_structure.copy()
    current_structure.xyz_df = xyz(current_structure)
    current_structure.load_experimental_from_file(experimental_G_csv)
    current_error = current_structure.prdf_error
    nsteps = 0
    c_error = "{:.5E}".format(current_error)
    print(f"Step {nsteps}. Error = {c_error}.")
    counter = []
    while nsteps < max_steps:
        nsteps += 1

        # TODO apply with validtaion
        transformer = transformation_objects[0]  # just grab the first transformation

        trial_structure = current_structure.copy()

        trial_structure.xyz_df = xyz(current_structure)

        new_structure = transformer.apply_transformation(trial_structure)

        is_valid = True  # true until proven otherwise
        for validator in validator_objects:
            if not validator.check_structure(new_structure):
                is_valid = False
                break  # one failure is enough to stop and reject the structure
        if not is_valid:
            print(f"Step {nsteps}. Move not valid.")
            continue  # restart the while loop

        """ DASK LOOP NOTES """
        # from dask.distributed import Client
        # client = Client()
        #
        # failed_cycles = 0
        # new_structure = False
        # while not new_structure:
        #     futures = [client.submit(make_candidate_structure, current_structure, validator_objects, transformer, pure=False) for n in range(1000)]
        #     for future in futures:
        #         new_structure = future.result()
        #         if new_structure:
        #             break
        #     for future in futures:
        #         future.cancel()
        #     if not new_structure:
        #         print("Failed to find valid structure with 1000 attempts. Trying again.")
        #         failed_cycles += 1
        #         if failed_cycles >= 10:
        #             print("Critical failure. Returning most recent structure")
        #             return current_structure
        # def make_candidate_structure(current_structure, validator_objects, transformer):
        #     new_structure = transformer.apply_transformation(current_structure)
        #     is_valid = True  # true until proven otherwise
        #     for validator in validator_objects:
        #         if not validator.check_structure(new_structure):
        #             is_valid = False
        #             break  # one failure is enough to stop and reject the structure
        #     if not is_valid:
        #         return False
        #     return new_structure

        counter.append(nsteps)

        new_structure.load_experimental_from_file(experimental_G_csv)
        new_error = new_structure.prdf_error
        new_e = "{:.5E}".format(new_error)
        ##  ^^ Wait for results from DASK

        keep_new = True
        if new_error < current_error:
            # accept new structure
            keep_new = True
            print(f"Step {nsteps}. Error improved, error = {new_e}.")
        else:
            # accept new structure with some probability or just restart the loop
            probability = exp(-1 * (abs(new_error - current_error)) / error_constant)
            if random() < probability:
                keep_new = True
                print(
                    f"Step {nsteps}. Error is worse but accepting move, error = {new_e}."
                )
            else:
                keep_new = False
                print(f"Step {nsteps}. Error is worse, rejecting move.")

        if keep_new:
            current_structure = new_structure
            current_error = new_error
            error_list.append(new_error)

    output_structure = current_structure
    output_structure.to(fmt="POSCAR", filename="output.vasp")
    print(f"counter = {counter}")
    return output_structure


# structure = run_rmc()
# structure.to(filename="out.cif")


def xyz(structure):
    import pandas as pd

    data = []
    for i, site in enumerate(structure.sites):
        temp = [
            site.coords[0],
            site.coords[1],
            site.coords[2],
            site.species_string,
        ]
        data.append(temp)
    labels = ["x", "y", "z", "el"]

    df = pd.DataFrame(data, columns=labels)

    df_x = df.copy().sort_values("x")
    df_y = df.copy().sort_values("y")
    df_z = df.copy().sort_values("z")

    return {"df_x": df_x, "df_y": df_y, "df_z": df_z}
