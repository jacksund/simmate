# -*- coding: utf-8 -*-

from pymatgen import Structure

from simmate.workflows.diffusion.utilities import run_vasp_custodian

structure = Structure.from_file("NaCl.cif")
structure = structure.get_primitive_structure()
structure = structure.copy(sanitize=True)

# These are the settings I've changed relative to MPStaticSet, where the ones
# still commented out are ones I'd consider changing if I'm doing a lower-quality
# calculation.
custom_incar = dict(
    EDIFF_PER_ATOM=5.0e-05,  # was EDIFF_PER_ATOM=5.0e-05
    # ENCUT=520, # was 520 --> reduced for fast rough calcs
    # ISPIN=2,  # was 2 --> spin-polarized turned off for rough calcs
    # LASPH=True,  # was True --> turned off for rough calcs.
    ALGO="Fast",  # Fast for geom_opt, Normal for static
    LDAUPRINT=0,  # was 1 --> Turned off verbosity of +U routines
    LORBIT=None,  # was 11 --> Turned off writing of PROCAR and DOSCAR
    LAECHG=False,  # don't write out the  AECCARs
    # LCHARG=False,  # don't write out the CHG or CHGCAR -- I keep this for custodian
    LVTOT=False,  # don't write the LOCPOT
    # KSPACING=0.5,
    NPAR=4,  # for parallel efficiency
    # IVDW=11,  # use DFT-D3 corrections
    ISYM=1,  # Turn off symmetry for vacancy-based diffusion calcs
)

run_vasp_custodian(
    structure,
    errorhandler_settings="default",
    vasp_cmd="mpirun -n 30 vasp",
    gamma_vasp_cmd="mpirun -n 30 vasp_gamma",
    custom_incar={},
    reciprocal_density=64,
)
