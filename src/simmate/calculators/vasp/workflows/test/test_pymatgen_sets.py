# -*- coding: utf-8 -*-

import pytest
from pymatgen.analysis.diffusion.neb.io import MVLCINEBEndPointSet, MVLCINEBSet
from pymatgen.io.vasp.sets import MITNEBSet  # MVLNPTMDSet,
from pymatgen.io.vasp.sets import (
    MITMDSet,
    MITRelaxSet,
    MPHSEBSSet,
    MPHSERelaxSet,
    MPMDSet,
    MPMetalRelaxSet,
    MPNMRSet,
    MPNonSCFSet,
    MPRelaxSet,
    MPScanRelaxSet,
    MPScanStaticSet,
    MPStaticSet,
    MVLElasticSet,
    MVLGBSet,
)

from simmate.calculators.vasp.inputs import Incar, Potcar
from simmate.calculators.vasp.workflows.all import (  # Dynamics__Vasp__MvlNpt,
    Diffusion__Vasp__NebFromImagesMit,
    Diffusion__Vasp__NebFromImagesMvlCi,
    Dynamics__Vasp__Matproj,
    Dynamics__Vasp__Mit,
    Relaxation__Vasp__Matproj,
    Relaxation__Vasp__MatprojHse,
    Relaxation__Vasp__MatprojMetal,
    Relaxation__Vasp__MatprojScan,
    Relaxation__Vasp__Mit,
    Relaxation__Vasp__MvlGrainboundary,
    Relaxation__Vasp__MvlNebEndpoint,
    Relaxation__Vasp__MvlSlab,
    StaticEnergy__Vasp__Matproj,
    StaticEnergy__Vasp__MatprojScan,
)
from simmate.calculators.vasp.workflows.elastic.mvl import Elastic__Vasp__Mvl

# extras that are hidden from the all endpoint
# NOTE: these imports are long/ugly because we hide the imports from users --
# and instead point them to higher-level workflows that call these.
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure_hse import (
    ElectronicStructure__Vasp__MatprojBandStructureHse,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states_hse import (
    ElectronicStructure__Vasp__MatprojDensityOfStatesHse,
)
from simmate.calculators.vasp.workflows.nuclear_magnetic_resonance.all import (
    Nmr__Vasp__MatprojChemicalShifts,
    Nmr__Vasp__MatprojFieldGradient,
)
from simmate.conftest import make_dummy_files
from simmate.toolkit.diffusion import MigrationImages

MD_KWARGS = {
    "start_temp": 300,
    "end_temp": 1200,
    "nsteps": 10000,
}


@pytest.mark.pymatgen
@pytest.mark.parametrize(
    "simmate_workflow, pymatgen_set, pymatgen_kwargs",
    [
        (Relaxation__Vasp__Matproj, MPRelaxSet, {}),
        (Relaxation__Vasp__Mit, MITRelaxSet, {}),
        (Relaxation__Vasp__MatprojHse, MPHSERelaxSet, {}),
        (Relaxation__Vasp__MatprojMetal, MPMetalRelaxSet, {}),
        (Relaxation__Vasp__MatprojScan, MPScanRelaxSet, {}),
        (Relaxation__Vasp__MvlNebEndpoint, MVLCINEBEndPointSet, {}),
        (Relaxation__Vasp__MvlGrainboundary, MVLGBSet, {"slab_mode": False}),
        (Relaxation__Vasp__MvlSlab, MVLGBSet, {"slab_mode": True}),
        (StaticEnergy__Vasp__Matproj, MPStaticSet, {}),
        (StaticEnergy__Vasp__MatprojScan, MPScanStaticSet, {}),
        (Dynamics__Vasp__Mit, MITMDSet, MD_KWARGS),
        (Dynamics__Vasp__Matproj, MPMDSet, MD_KWARGS),
        # MVL-NPT MD requires POTCARs to be configured for pymatgen. need a workaround.
        # (Dynamics__Vasp__MvlNpt, MVLNPTMDSet, MD_KWARGS),
        (
            ElectronicStructure__Vasp__MatprojBandStructureHse,
            MPHSEBSSet,
            {"mode": "line"},
        ),
        (
            ElectronicStructure__Vasp__MatprojBandStructure,
            MPNonSCFSet,
            {"mode": "line"},
        ),
        (
            ElectronicStructure__Vasp__MatprojDensityOfStates,
            MPNonSCFSet,
            {"mode": "uniform"},
        ),
        (
            ElectronicStructure__Vasp__MatprojDensityOfStatesHse,
            MPHSEBSSet,
            {"mode": "uniform"},
        ),
        (Nmr__Vasp__MatprojChemicalShifts, MPNMRSet, {"mode": "cs"}),
        (Nmr__Vasp__MatprojFieldGradient, MPNMRSet, {"mode": "efg"}),
        (Elastic__Vasp__Mvl, MVLElasticSet, {}),
    ],
)
def test_pymatgen_input_sets(
    structure,
    tmp_path,
    mocker,
    simmate_workflow,
    pymatgen_set,
    pymatgen_kwargs,
):
    """
    Many of the presets implemented are ported directly from pymatgen, so these
    tests simply confirm that the inputs give the same INCAR results.
    """

    # set filenames
    incar_simmate_name = tmp_path / "INCAR"
    incar_pymatgen_name = tmp_path / "INCAR_pmg"

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    potcar_filename = tmp_path / "POTCAR"
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # write both inputs
    simmate_workflow.setup(structure=structure, directory=tmp_path)
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
    if "EDIFF" in diff and "EDIFF__per_atom" in simmate_workflow.incar:
        ediff_simmate, ediff_pymatgen = diff["EDIFF"]
        percent_diff = (ediff_pymatgen - ediff_simmate) / ediff_pymatgen
        if abs(percent_diff) < 1:
            diff.pop("EDIFF")

    # ensure incars are the same (there are no differences)
    assert diff == {}


@pytest.mark.pymatgen
@pytest.mark.parametrize(
    "simmate_workflow, pymatgen_set, pymatgen_kwargs",
    [
        (Diffusion__Vasp__NebFromImagesMit, MITNEBSet, {}),
        (Diffusion__Vasp__NebFromImagesMvlCi, MVLCINEBSet, {}),
    ],
)
def test_pymatgen_input_sets_neb(
    structure,
    tmp_path,
    mocker,
    simmate_workflow,
    pymatgen_set,
    pymatgen_kwargs,
):
    """
    This is a copy/paste of the test method above, but this is for sets that
    accept multiple structures as inputs (such as NEB sets)
    """

    # set filenames
    incar_simmate_name = tmp_path / "INCAR"
    incar_pymatgen_name = tmp_path / "INCAR_pmg"

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    potcar_filename = tmp_path / "POTCAR"
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # write both inputs. We just copy the same structure 3 times because we
    # don't really care what the POSCARs look like -- just the INCARs
    simmate_workflow.setup(
        migration_images=MigrationImages([structure] * 3),
        directory=tmp_path,
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
    if "EDIFF" in diff and "EDIFF__per_atom" in simmate_workflow.incar:
        ediff_simmate, ediff_pymatgen = diff["EDIFF"]
        percent_diff = (ediff_pymatgen - ediff_simmate) / ediff_pymatgen
        if abs(percent_diff) < 1:
            diff.pop("EDIFF")

    # ensure incars are the same (there are no differences)
    assert diff == {}
