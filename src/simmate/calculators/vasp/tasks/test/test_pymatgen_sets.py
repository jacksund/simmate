# -*- coding: utf-8 -*-

import os
import pytest

from simmate.conftest import make_dummy_files
from simmate.calculators.vasp.inputs import Incar, Potcar

# -----------------------------------------------------------------------------
# Simmate tasks and their corresponding pymatgen sets are paired below

from simmate.calculators.vasp.tasks.relaxation import MatProjRelaxation
from pymatgen.io.vasp.sets import MPRelaxSet

from simmate.calculators.vasp.tasks.relaxation import MITRelaxation
from pymatgen.io.vasp.sets import MITRelaxSet

from simmate.calculators.vasp.tasks.static_energy import MatProjStaticEnergy
from pymatgen.io.vasp.sets import MPStaticSet

from simmate.calculators.vasp.tasks.dynamics import MITDynamics
from pymatgen.io.vasp.sets import MITMDSet

from simmate.calculators.vasp.tasks.dynamics import MatProjDynamics
from pymatgen.io.vasp.sets import MPMDSet

from simmate.calculators.vasp.tasks.relaxation import MatProjHSERelaxation
from pymatgen.io.vasp.sets import MPHSERelaxSet

from simmate.calculators.vasp.tasks.band_structure import MatProjHSEBandStructure
from simmate.calculators.vasp.tasks.density_of_states import MatProjHSEDensityOfStates
from pymatgen.io.vasp.sets import MPHSEBSSet

from simmate.calculators.vasp.tasks.band_structure import MatProjBandStructure
from simmate.calculators.vasp.tasks.density_of_states import MatProjDensityOfStates
from pymatgen.io.vasp.sets import MPNonSCFSet

from simmate.calculators.vasp.tasks.relaxation import MatProjMetalRelaxation
from pymatgen.io.vasp.sets import MPMetalRelaxSet

# -----------------------------------------------------------------------------

MD_KWARGS = {
    "start_temp": 300,
    "end_temp": 1200,
    "nsteps": 10000,
}


@pytest.mark.pymatgen
@pytest.mark.parametrize(
    "simmate_task, pymatgen_set, pymatgen_kwargs",
    [
        (MatProjRelaxation, MPRelaxSet, {}),
        (MITRelaxation, MITRelaxSet, {}),
        (MITRelaxation, MITRelaxSet, {}),
        (MatProjStaticEnergy, MPStaticSet, {}),
        (MatProjHSERelaxation, MPHSERelaxSet, {}),
        (MatProjMetalRelaxation, MPMetalRelaxSet, {}),
        (MITDynamics, MITMDSet, MD_KWARGS),
        (MatProjDynamics, MPMDSet, MD_KWARGS),
        (MatProjHSEBandStructure, MPHSEBSSet, {"mode": "line"}),
        (MatProjBandStructure, MPNonSCFSet, {"mode": "line"}),
        (MatProjDensityOfStates, MPNonSCFSet, {"mode": "uniform"}),
        (MatProjHSEDensityOfStates, MPHSEBSSet, {"mode": "uniform"}),
    ],
)
def test_pymatgen_input_sets(
    structure,
    tmpdir,
    mocker,
    simmate_task,
    pymatgen_set,
    pymatgen_kwargs,
):
    """
    Many of the presets implemented are ported directly from pymatgen, so these
    tests simply confirm that the inputs give the same INCAR results.
    """

    # set filenames
    incar_simmate_name = os.path.join(tmpdir, "INCAR")
    incar_pymatgen_name = os.path.join(tmpdir, "INCAR_pmg")

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    potcar_filename = os.path.join(tmpdir, "POTCAR")
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # write both inputs
    simmate_task().setup(structure=structure, directory=tmpdir)
    pymatgen_set(structure, **pymatgen_kwargs).incar.write_file(incar_pymatgen_name)

    # load incar
    incar_simmate = Incar.from_file(incar_simmate_name)
    incar_pymatgen = Incar.from_file(incar_pymatgen_name)

    # compare
    diff = incar_simmate.compare_incars(incar_pymatgen)["Different"]
    # ignore kpoints input for now
    diff.pop("KSPACING", None)

    # in EDIFF__per_atom, there are sometimes rounding issues.
    # We say there is no difference if they are within 100% error. This may
    # seem like a large error, but it is meant to encompass differences like
    # {'EDIFF': (4e-06, 1e-05)} where pymatgen rounded significantly. There
    # really isn't an issue unless EDIFF is off by a factor of 10 (1000%)
    if "EDIFF" in diff and "EDIFF__per_atom" in simmate_task.incar:
        ediff_simmate, ediff_pymatgen = diff["EDIFF"]
        percent_diff = (ediff_pymatgen - ediff_simmate) / ediff_pymatgen
        if abs(percent_diff) < 1:
            diff.pop("EDIFF")

    # ensure incars are the same (there are no differences)
    assert diff == {}
