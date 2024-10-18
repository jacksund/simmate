# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.relaxation.quality02 import Relaxation__QuantumEspresso__Quality02


class Relaxation__QuantumEspresso__Quality03(Relaxation__QuantumEspresso__Quality02):
    """
    Runs a slightly rough Quantum Espresso geometry optimization with fixed lattice 
    volume.
    
    `Quality 03` indicates that on a scale from 00 to 04, these are ranked 03 in
    quality (with 04 being the highest quality).

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a fourth step.
    """
    
    description_doc_short = "less bare-bones settings for randomly-created structures"

    system = dict(
        ibrav=0, # indicates crystal axis is provided in input
        nat__auto=True, # automatically set number of atoms
        ntyp__auto=True, # automatically set number of types of atoms
        ecutwfc__auto="efficiency_1.1", # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_1.1", # automatically select energy cutoff for charge density/potential
        # We don't know if we have a metal or non-metal so we make a guess here.
        # !!! This guess could be dangerous without handlers
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing", # use smearing
                smearing="methfessel-paxton", # equivalent to ISMEAR=1
                degauss=0.06, # equivalent to SIGMA
            ),
            "non-metal": dict(
                occupations="smearing", # Should we still use smearing here like we would in vasp?
                smearing="gaussian", # equivalent to ISMEAR=0
                degauss=0.05,
            ),
        },
    )

    electrons = dict(
        diagonalization="david", # equivalent to ALGO = Normal
        mixing_mode="plain", 
        mixing_beta=0.7, # mixing factor for self-consistency
        conv_thr="1.0e-4", # convergence threshold for SCF cycle
    )


