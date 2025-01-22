# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.relaxation import (
    Relaxation__QuantumEspresso__Quality00,
    Relaxation__QuantumEspresso__Quality01,
)
from simmate.engine.staged_workflow import StagedWorkflow


#!!! Need to update settings and get LDA pseudopotentials
class Relaxation__QuantumEspresso__Lda00(Relaxation__QuantumEspresso__Quality00):
    """
    Runs a VERY rough Quantum Espresso geometry optimization with fixed lattice
    volume.`LDA00` indicates these are absolute lowest quality settings
    used in our available presets for LDA.

    This should only be run in the context of a staged training
    workflow and will not return reasonable results. It is only designed for
    testing and learning.
    """

    description_doc_short = "barest-bones settings for randomly-created structures"

    # We use low quality PBE pseudopotentials
    # !!! We should really use LDA PPs, but since this caculation will be VERY
    # low quality anyways it's fine for now
    psuedo_mappings_set = "SSSP_PBE_EFFICIENCY"

    system = dict(
        ibrav=0,  # indicates crystal axis is provided in input
        nat__auto=True,  # automatically set number of atoms
        ntyp__auto=True,  # automatically set number of types of atoms
        ecutwfc__auto="efficiency_0.667",  # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_0.667",  # automatically select energy cutoff for charge density/potential
        input_dft="lda",  # !!! We should get PPs for LDA
        # We don't know if we have a metal or non-metal so we make a guess here.
        # !!! This guess could be dangerous without handlers
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing",  # use smearing
                smearing="methfessel-paxton",  # equivalent to ISMEAR=1
                degauss=0.1,  # equivalent to SIGMA
            ),
            "non-metal": dict(
                occupations="smearing",  # Should we still use smearing here like we would in vasp?
                smearing="gaussian",  # equivalent to ISMEAR=0
                degauss=0.05,
            ),
        },
    )


class Relaxation__QuantumEspresso__Lda01(Relaxation__QuantumEspresso__Quality01):
    """
    Runs a VERY rough Quantum Espresso geometry optimization.
    `LDA01` indicates these are poor quality settings used in our available
    presets for LDA.

    This should only be run in the context of a staged training
    workflow and will not return reasonable results. It is only designed for
    testing and learning.
    """

    description_doc_short = "barest-bones settings for randomly-created structures"

    system = dict(
        ibrav=0,  # indicates crystal axis is provided in input
        nat__auto=True,  # automatically set number of atoms
        ntyp__auto=True,  # automatically set number of types of atoms
        ecutwfc__auto="efficiency_0.8",  # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_0.8",  # automatically select energy cutoff for charge density/potential
        input_dft="lda",
        # We don't know if we have a metal or non-metal so we make a guess here.
        # !!! This guess could be dangerous without handlers
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing",  # use smearing
                smearing="methfessel-paxton",  # equivalent to ISMEAR=1
                degauss=0.1,  # equivalent to SIGMA
            ),
            "non-metal": dict(
                occupations="smearing",  # Should we still use smearing here like we would in vasp?
                smearing="gaussian",  # equivalent to ISMEAR=0
                degauss=0.05,
            ),
        },
    )


class StaticEnergy__QuantumEspresso__Lda02(Relaxation__QuantumEspresso__Lda01):
    """
    Runs a VERY rough Quantum Espresso static energy calc.
    `LDA01` indicates these are poor quality settings
    used in our available presets for LDA.

    This should only be run in the context of a staged training
    workflow and will not return reasonable results. It is only designed for
    testing and learning.
    """

    control = dict(
        pseudo_dir__auto=True,  # uses the default directory for pseudopotentials
        restart_mode="from_scratch",  # start from new calc rather than restart
        calculation="scf",  # perform static energy calc
        tstress=True,  # calculate stress
        tprnfor=True,  # calculate forces
    )
    system = dict(
        ibrav=0,  # indicates crystal axis is provided in input
        nat__auto=True,  # automatically set number of atoms
        ntyp__auto=True,  # automatically set number of types of atoms
        ecutwfc__auto="efficiency_0.8",  # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_0.8",  # automatically select energy cutoff for charge density/potential
        occupations="tetrahedra",  # was "smearing - methfessel-paxton" for metals, "smearing - gaussian" for non-metals
        degauss=0.05,  # Not sure this does anything with "tetrahedra". Was 0.05 for non-metals, 0.1 for metals
    )


class StaticEnergy__QuantumEspresso__EvoTutorial(StagedWorkflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This workflow is designed exclusively for testing/tutorials where it is
    desireable to have calculations take very little time. The results
    will be VERY unreasonable.
    """

    # !!! Needs to be implemented
    exclude_from_archives = []

    description_doc_short = "runs a series of very low quality relaxations"

    subworkflow_names = [
        Relaxation__QuantumEspresso__Lda00,
        Relaxation__QuantumEspresso__Lda01,
        StaticEnergy__QuantumEspresso__Lda02,
    ]
