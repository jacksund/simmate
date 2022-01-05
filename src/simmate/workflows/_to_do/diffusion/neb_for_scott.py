# -*- coding: utf-8 -*-

import os

from prefect import task, Flow, Parameter

from pymatgen.core.structure import Structure

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.error_handlers.tetrahedron_mesh import TetrahedronMesh
from simmate.calculators.vasp.error_handlers.eddrmm import Eddrmm
from simmate.calculators.vasp.tasks.nudged_elastic_band import NudgedElasticBandTask


relax_structure = VaspTask(
    incar=dict(
        ALGO="Normal",  # TEMPORARY SWITCH FROM Fast
        EDIFF=1.0e-05,
        EDIFFG=-0.02,  # From MVL's set
        ENCUT=520,
        IBRION=2,
        ICHARG=1,
        ISIF=3,
        ISMEAR=2,  ## changed for metal
        ISPIN=2,
        ISYM=0,
        # LDAU --> These parameters are excluded for now.
        LORBIT=11,
        LREAL="False",
        LWAVE=False,
        NELM=200,
        NELMIN=6,
        NSW=99,  # !!! Changed to static energy for testing
        PREC="Accurate",
        SIGMA=0.2,
        KSPACING=0.4,  # --> This is VASP default and not the same as pymatgen
    ),
    functional="PBE",
    error_handlers=[TetrahedronMesh(), Eddrmm()],
)

# FOR NEB RELAXATION
run_neb = NudgedElasticBandTask(
    incar=dict(
        # https://github.com/materialsproject/pymatgen/blob/v2022.0.9/pymatgen/io/vasp/MPRelaxSet.yaml
        ALGO="Normal",  # TEMPORARY SWITCH FROM Fast
        EDIFF=1.0e-05,
        EDIFFG=-0.02,  # From MVL's set
        ENCUT=520,
        # IBRION=2, --> overwritten by MITNEBSet below
        ICHARG=1,
        ISIF=2,  # fixed lattice
        ISMEAR=-5,
        ISPIN=2,
        ISYM=0,
        # LDAU --> These parameters are excluded for now.
        LORBIT=11,
        LREAL="False",
        LWAVE=False,
        NELM=200,
        NELMIN=6,
        NSW=99,  # !!! Changed to static energy for testing
        PREC="Accurate",
        SIGMA=0.2,
        KSPACING=0.4,  # --> This is VASP default and not the same as pymatgen
        # These settings are from MITNEBSet
        # https://github.com/materialsproject/pymatgen/blob/v2022.0.9/pymatgen/io/vasp/sets.py#L2376-L2491
        # IMAGES=len(structures) - 2, --> set inside task
        IBRION=1,
        # ISYM=0, --> duplicate of setting above
        LCHARG=False,
    )
)


@task(nout=3)
def load_images_from_files(directory="source_structures", nimages=21):

    structures = []
    for nposcar in range(nimages):
        filename = os.path.join(directory, f"POSCAR_{str(nposcar).zfill(2)}")
        structure = Structure.from_file(filename)
        structures.append(structure)

    # returns start_image, [midpoint_images], end_image
    return structures[0], structures[1:-1], structures[-1]


# now make the overall workflow
with Flow("NEB Analysis") as workflow:

    # These are the input parameters for the overall workflow
    # images = Parameter("images")
    # directory = Parameter("directory", default=None)
    vasp_cmd = Parameter("vasp_command", default="vasp_std > vasp.out")

    # grab our start/end structures of a target supercell size
    start_structure, images, end_structure = load_images_from_files()

    # Relax the start/end images
    start_structure_relaxed, corrections = relax_structure(
        structure=start_structure,
        directory="start_image_relaxation",
        command=vasp_cmd,
    )
    end_structure_relaxed, corrections = relax_structure(
        structure=end_structure,
        directory="end_image_relaxation",
        command=vasp_cmd,
    )

    # Relax all images using NEB
    run_neb(
        structure=[start_structure_relaxed] + images + [end_structure_relaxed],
        command=vasp_cmd,
    )

# --------------------------

workflow.run(vasp_command="mpirun -n 76 vasp_std > vasp.out")
