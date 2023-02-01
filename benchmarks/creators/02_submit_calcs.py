# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Composition, Structure
from simmate.utilities import get_directory
from simmate.workflows.utilities import get_workflow

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
compositions = [Composition(c) for c in COMPOSITIONS_TO_TEST]

NSAMPLES_PER_COMPOSITION = 500

CREATORS_TO_TEST = [
    # "Simmate", done
    # "Simmate (strict)", done
    # "XtalOpt", done
    # "ASE", done
    # "PyXtal", done
    # "GASP", done
    # "AIRSS", done
    # "USPEX", done
    # "CALYPSO", done
]

parent_dir = get_directory("creator_benchmarks")
workflow_static = get_workflow("static-energy.vasp.quality04")
workflow_relax = get_workflow("relaxation.vasp.staged")

for creator_name in CREATORS_TO_TEST:
    for composition in compositions:
        directory = parent_dir / creator_name / str(composition)

        if not directory.exists():
            continue

        for file in track(directory.iterdir()):
            # skip if was submitted already
            if workflow_static.all_results.filter(source__file=str(file)).exists():
                continue

            structure = Structure.from_file(file)

            workflow_static.run_cloud(
                structure=structure,
                source={
                    "creator": creator_name,
                    "file": str(file),
                    "is_initial": True,
                },
                command="mpirun -n 4 vasp_std > vasp.out",
                compress_output=True,
            )

            workflow_relax.run_cloud(
                structure=structure,
                source={
                    "creator": creator_name,
                    "file": str(file),
                },
                command="mpirun -n 4 vasp_std > vasp.out",
                compress_output=True,
            )
