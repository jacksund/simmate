# -*- coding: utf-8 -*-

import os
import pytest

from simmate.conftest import make_dummy_files
from simmate.calculators.vasp.inputs import Incar, Potcar
from simmate.toolkit.diffusion import MigrationImages

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

from simmate.calculators.vasp.tasks.nuclear_magnetic_resonance import (
    MatProjNMRChemicalShifts,
    MatProjNMRElectricFieldGradiant,
)
from pymatgen.io.vasp.sets import MPNMRSet

from simmate.calculators.vasp.tasks.elastic import MatVirtualLabElastic
from pymatgen.io.vasp.sets import MVLElasticSet

from simmate.calculators.vasp.tasks.relaxation import (
    MatVirtualLabGrainBoundaryRelaxation,
    MatVirtualLabSlabRelaxation,
)
from pymatgen.io.vasp.sets import MVLGBSet

from simmate.calculators.vasp.tasks.nudged_elastic_band import MITNudgedElasticBand
from pymatgen.io.vasp.sets import MITNEBSet

from simmate.calculators.vasp.tasks.nudged_elastic_band import (
    MatVirtualLabClimbingImageNudgedElasticBand,
)
from pymatgen.analysis.diffusion.neb.io import MVLCINEBSet

from simmate.calculators.vasp.tasks.relaxation import NEBEndpointRelaxation
from pymatgen.analysis.diffusion.neb.io import MVLCINEBEndPointSet

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
        (NEBEndpointRelaxation, MVLCINEBEndPointSet, {}),
        (MITDynamics, MITMDSet, MD_KWARGS),
        (MatProjDynamics, MPMDSet, MD_KWARGS),
        (MatProjHSEBandStructure, MPHSEBSSet, {"mode": "line"}),
        (MatProjBandStructure, MPNonSCFSet, {"mode": "line"}),
        (MatProjDensityOfStates, MPNonSCFSet, {"mode": "uniform"}),
        (MatProjHSEDensityOfStates, MPHSEBSSet, {"mode": "uniform"}),
        (MatProjNMRChemicalShifts, MPNMRSet, {"mode": "cs"}),
        # (MatProjNMRElectricFieldGradiant, MPNMRSet, {"mode": "efg"}),
        # MPNMRSet is bugged at the moment: https://github.com/materialsproject/pymatgen/pull/2509
        (MatVirtualLabElastic, MVLElasticSet, {}),
        (MatVirtualLabGrainBoundaryRelaxation, MVLGBSet, {"slab_mode": False}),
        (MatVirtualLabSlabRelaxation, MVLGBSet, {"slab_mode": True}),
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


@pytest.mark.pymatgen
@pytest.mark.parametrize(
    "simmate_task, pymatgen_set, pymatgen_kwargs",
    [
        (MITNudgedElasticBand, MITNEBSet, {}),
        (MatVirtualLabClimbingImageNudgedElasticBand, MVLCINEBSet, {}),
    ],
)
def test_pymatgen_input_sets_neb(
    structure,
    tmpdir,
    mocker,
    simmate_task,
    pymatgen_set,
    pymatgen_kwargs,
):
    """
    This is a copy/paste of the test method above, but this is for sets that
    accept multiple structures as inputs (such as NEB sets)
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

    # write both inputs. We just copy the same structure 3 times because we
    # don't really care what the POSCARs look like -- just the INCARs
    simmate_task().setup(
        structure=None,
        structures=MigrationImages([structure] * 3),
        directory=tmpdir,
    )
    pymatgen_set([structure] * 3, **pymatgen_kwargs).incar.write_file(
        incar_pymatgen_name
    )

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
