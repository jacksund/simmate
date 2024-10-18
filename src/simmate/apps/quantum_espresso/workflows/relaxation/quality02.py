# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.base import PwscfWorkflow


class Relaxation__QuantumEspresso__Quality02(PwscfWorkflow):
    """
    Runs a rough Quantum Espresso geometry optimization with fixed lattice 
    volume.`Quality 02` indicates these are absolute lowest quality settings 
    used in our available presets.

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a third step.
    """
    
    description_doc_short = "slightly less bare-bones settings for randomly-created structures"
    
    # The settings are made to mirror the settings in relaxation.vasp.quality00.
    # Some settings do not have direct parallels or are implemented differently: 
    # e.g. IBRION, POTIM, LWAVE, LCHARG, EDIFFG
       
    # We use the relatively low quality pseudopotentials (labeled with efficiencty
    # rather than accuracy)
    psuedo_mappings_set = "SSSP_PBE_EFFICIENCY"
    
    # Make the unitcell relatively cubic before relaxing
    standardize_structure = "primitive-LLL"
    symmetry_precision = 0.1
    
    control = dict(
        pseudo_dir__auto=True, # uses the default directory for pseudopotentials
        restart_mode="from_scratch", # start from new calc rather than restart
        calculation="relax", # perform geometry relaxation with fixed cell
        tstress=True, # calculate stress
        tprnfor=True, # calculate forces
        nstep=100, # maximum number of ionic steps
    )

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
        conv_thr="1.0e-3", # convergence threshold for SCF cycle
    )
    
    ions = dict(
        ion_dynamics="bfgs", #ionic relaxation method akin to IBRION
    )


    k_points = dict(
        spacing=0.5,
        gamma_centered=True,
    )


