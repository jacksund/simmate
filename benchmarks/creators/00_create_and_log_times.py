# -*- coding: utf-8 -*-

import logging
from timeit import default_timer as time

import numpy
import pandas
from rich.progress import track

from simmate.toolkit import Composition
from simmate.utilities import get_directory

# BUG: from time import time --> incorrectly gives 0 seconds in some cases, so
# therefore use the timeit module instead

# Disable logging throughout for cleaner output
logger = logging.getLogger()
logger.disabled = True

# Establish the compositions and settings that we are testing.
# Here is a list of our control (reduced) compositions and the total atom
# counts for their known global minimum structures:
COMPOSITIONS_TO_TEST = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    "Si4O8",
    "Al4O6",
    "Si4N4O2",
    "Sr4Si4N8",
    "Mg4Si4O12",
]

NSAMPLES_PER_COMPOSITION = 500


def time_test_creation(creator_class, creator_kwargs):
    compositions = [Composition(c) for c in COMPOSITIONS_TO_TEST]

    # build parent directory
    parent_dir = get_directory("creator_benchmarks")
    directory = get_directory(parent_dir / creator_class.name)

    all_comp_times = []

    for composition in compositions:
        # BUG: some creators fail for specific compositions
        if str(composition) == "Fe1" and creator_class.name == "ASE":
            all_comp_times.append([None] * NSAMPLES_PER_COMPOSITION)
            continue

        comp_directory = get_directory(directory / str(composition))

        creator = creator_class(composition, **creator_kwargs)

        if creator_class.name in [
            # "XtaloptStructure",
            "USPEX",
            "CALYPSO",
        ]:
            start = time()
            structures = creator.create_structures(NSAMPLES_PER_COMPOSITION)
            end = time()
            average_time = (end - start) / NSAMPLES_PER_COMPOSITION
            all_comp_times.append([average_time] * NSAMPLES_PER_COMPOSITION)
            for n, structure in enumerate(structures):
                structure.to(
                    filename=str(comp_directory / f"{n}.cif"),
                    fmt="cif",
                )
            continue

        single_comp_times = []
        for n in track(
            range(NSAMPLES_PER_COMPOSITION),
            description=f"{creator_class.name} - {composition}",
        ):
            structure = False
            attempt = 1
            while not structure:
                attempt += 1
                start = time()
                structure = creator.create_structure()
                end = time()
            single_comp_times.append(end - start)
            structure.to(
                filename=str(comp_directory / f"{n}.cif"),
                fmt="cif",
            )
        all_comp_times.append(single_comp_times)

    df = pandas.DataFrame(
        numpy.transpose(all_comp_times),
        columns=COMPOSITIONS_TO_TEST,
    )
    df.to_csv(directory / "times.csv")

    # attach data for future reference
    creator_class.benchmark_results = df

    return df


from simmate.toolkit.creators.structure.random_symmetry import RandomSymStructure
from simmate.toolkit.creators.structure.third_party.airss import AirssStructure
from simmate.toolkit.creators.structure.third_party.ase import AseStructure
from simmate.toolkit.creators.structure.third_party.calypso import CalypsoStructure
from simmate.toolkit.creators.structure.third_party.gasp import GaspStructure
from simmate.toolkit.creators.structure.third_party.pyxtal import PyXtalStructure
from simmate.toolkit.creators.structure.third_party.uspex import UspexStructure
from simmate.toolkit.creators.structure.third_party.xtalopt import XtaloptStructure

RandomSymStructure.name = "Simmate"
# RandomSymStructure.name = "Simmate (strict)",  # 0.75 packing factor for dist cutoffs
XtaloptStructure.name = "XtalOpt"
AseStructure.name = "ASE"
PyXtalStructure.name = "PyXtal"
GaspStructure.name = "GASP"
AirssStructure.name = "AIRSS"
UspexStructure.name = "USPEX"
CalypsoStructure.name = "CALYPSO"

CREATORS_TO_TEST = [
    (
        RandomSymStructure,
        {
            "site_gen_options": {
                "lazily_generate_combinations": False,
            }
        },
    ),
    (
        XtaloptStructure,
        {
            "command": "/home/jacksund/Documents/github/randSpg/build/randSpg",
        },
    ),
    (AseStructure, {}),
    (PyXtalStructure, {}),
    (GaspStructure, {}),
    (AirssStructure, {}),
    (UspexStructure, {}),
    (CalypsoStructure, {}),
]

for creator_class, creator_kwargs in CREATORS_TO_TEST:
    time_test_creation(creator_class, creator_kwargs)
