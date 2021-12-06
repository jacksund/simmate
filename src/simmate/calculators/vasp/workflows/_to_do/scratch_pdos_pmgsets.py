# -*- coding: utf-8 -*-

from pymatgen.core.structure import Structure
from pymatgen.io.vasp.sets import MPStaticSet

structure = Structure.from_file("Y2C.cif")
structure = structure.get_primitive_structure()
calc = MPStaticSet(
    structure,
    user_incar_settings={
        # "NPAR": 4,
        "ISPIN": 2,
        "EDIFF": 0.00015000000000000001,
        "ICHARG": 2,
        "LAECHG": "False",
        "SYMPREC": 1e-8,  #!!! CUSTODIAN FIX - dont use unless needed
    },
)

# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

# Now run this calculation

print("Running vasp...")

# run vasp
import subprocess

subprocess.run(
    "module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out",
    shell=True,
)

subprocess.run(
    "cp CHG CHG_step1",
    shell=True,
)

# -----------------------------------------------------------------------------

from pymatgen.io.vasp.sets import MPNonSCFSet

calc = MPNonSCFSet.from_prev_calc(
    ".",
    user_incar_settings={
        # For band-decomposed charge densities
        "LPARD": True,  # Yes to doing band-decomposed charge densities
        "LSEPB": True,  # Rather than calculate bands separately and write to file, we combine all of them for energy range in EINT
        "NBMOD": -3,  # calculated partial charge density for only energys specified by EINT (sets EINT to vs Fermi Energy too)
        # "IBAND": ' '.join([str(n) for n in range(1,100)]),
        "EINT": "-9999 0",  # energy range to look at for decomposed charge density
        "ISYM": 0,  # turn off symmetry
        # "NBANDS": 50,
    },
    mode="uniform",
    copy_chgcar=False,
)

# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

# Now run this calculation

print("Running vasp...")

# run vasp
import subprocess

subprocess.run(
    "module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out",
    shell=True,
)


import os
from pymatgen.io.vasp.outputs import Chgcar

all_parchgs = [filename for filename in os.listdir() if "CHG" in filename]

for parchg in all_parchgs:
    try:
        chgcar = Chgcar.from_file(parchg)
        structure = chgcar.structure
        structure.append("H", [0.5, 0.5, 0.5])
        chgcar.write_file(parchg + "_empty")
    except:
        pass
