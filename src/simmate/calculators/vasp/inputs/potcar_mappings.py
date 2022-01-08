# -*- coding: utf-8 -*-

import os
from pathlib import Path

# grab the users set directory for all of their VASP POTCAR files
# TODO - for now, I assume that the directory is located in...
#   [home_directory] ~/simmate/vasp/Potentials
potcar_dir = os.path.join(Path.home(), "simmate", "vasp", "Potentials")


# This maps out where functional POTCARs are located. All of these
# files should be located in the same Potentals directory and follow
# the original folder structure provided by VASP.
FOLDER_MAPPINGS = {
    "LDA": os.path.join(potcar_dir, "LDA", "potpaw_LDA.54"),
    "PBE": os.path.join(potcar_dir, "PBE", "potpaw_PBE.54"),
    "PBE_GW": os.path.join(potcar_dir, "PBE", "potpaw_PBE.54"),
}

# We need to map which POTCAR to grab for each element based off of the type
# of calculation we are doing. To see how these were selected, you should look
# at the following:
#
#   Material's Project rational
#   https://wiki.materialsproject.org/Pseudopotentials_Choice
#
#   Pymatgen sets (look at the yaml files)
#   https://github.com/materialsproject/pymatgen/tree/v2020.12.31/pymatgen/io/vasp
#   For potential that use fewer electron (faster but lower quality), it's useful
#   to look at the MITRelaxSet.yaml, but MPRelaxSet's choices of higher electron
#   counts can give fast calculations (<1min) AND are appropriate for high-quality
#   calculations. Thus we go ahead with the more accurate ones as the default choice.
#
#   VASP recommendations
#   https://cms.mpi.univie.ac.at/vasp/vasp/Ultrasoft_pseudopotentials_supplied_with_VASP_package.html
#   Note, this webpage is outdated, but I don't see them move this information
#   into their new wiki...
#
#   Comparison of different potentials' accuracy
#   https://molmod.ugent.be/deltacodesdft

# TODO -- add LDA mappings. There's no example in Pymatgen that I see.

PBE_ELEMENT_MAPPINGS = {
    "Ac": "Ac",
    "Ag": "Ag",
    "Al": "Al",
    "Ar": "Ar",
    "As": "As",
    "Au": "Au",
    "B": "B",
    "Ba": "Ba_sv",
    "Be": "Be_sv",
    "Bi": "Bi",
    "Br": "Br",
    "C": "C",
    "Ca": "Ca_sv",
    "Cd": "Cd",
    "Ce": "Ce",
    "Cl": "Cl",
    "Co": "Co",
    "Cr": "Cr_pv",
    "Cs": "Cs_sv",
    "Cu": "Cu_pv",
    "Dy": "Dy_3",
    "Er": "Er_3",
    "Eu": "Eu",
    "F": "F",
    "Fe": "Fe_pv",
    "Ga": "Ga_d",
    "Gd": "Gd",
    "Ge": "Ge_d",
    "H": "H",
    "He": "He",
    "Hf": "Hf_pv",
    "Hg": "Hg",
    "Ho": "Ho_3",
    "I": "I",
    "In": "In_d",
    "Ir": "Ir",
    "K": "K_sv",
    "Kr": "Kr",
    "La": "La",
    "Li": "Li_sv",
    "Lu": "Lu_3",
    "Mg": "Mg_pv",
    "Mn": "Mn_pv",
    "Mo": "Mo_pv",
    "N": "N",
    "Na": "Na_pv",
    "Nb": "Nb_pv",
    "Nd": "Nd_3",
    "Ne": "Ne",
    "Ni": "Ni_pv",
    "Np": "Np",
    "O": "O",
    "Os": "Os_pv",
    "P": "P",
    "Pa": "Pa",
    "Pb": "Pb_d",
    "Pd": "Pd",
    "Pm": "Pm_3",
    "Pr": "Pr_3",
    "Pt": "Pt",
    "Pu": "Pu",
    "Rb": "Rb_sv",
    "Re": "Re_pv",
    "Rh": "Rh_pv",
    "Ru": "Ru_pv",
    "S": "S",
    "Sb": "Sb",
    "Sc": "Sc_sv",
    "Se": "Se",
    "Si": "Si",
    "Sm": "Sm_3",
    "Sn": "Sn_d",
    "Sr": "Sr_sv",
    "Ta": "Ta_pv",
    "Tb": "Tb_3",
    "Tc": "Tc_pv",
    "Te": "Te",
    "Th": "Th",
    "Ti": "Ti_pv",
    "Tl": "Tl_d",
    "Tm": "Tm_3",
    "U": "U",
    "V": "V_pv",
    "W": "W_pv",
    "Xe": "Xe",
    "Y": "Y_sv",
    "Yb": "Yb_2",
    "Zn": "Zn",
    "Zr": "Zr_sv",
}

# Another common mapping comes from the MIT project (pre-cursor to Materials Project)
# The POTCARs here are generally the ones with fewer electrons and convergence
# criteria is less tight. A lot of the elements are the same as above, so we
# just copy those element mappings and update the elements that are actaully
# lower quality here.
PBE_ELEMENT_MAPPINGS_LOW_QUALITY = PBE_ELEMENT_MAPPINGS.copy()
PBE_ELEMENT_MAPPINGS_LOW_QUALITY.update(
    {
        "Be": "Be",
        "Cr": "Cr",
        "Cu": "Cu",
        "Fe": "Fe",
        "Ga": "Ga",
        "Ge": "Ge",
        "Hf": "Hf",
        "In": "In",
        "Li": "Li",
        "Mg": "Mg",
        "Mn": "Mn",
        "Na": "Na",
        "Nd": "Nd",
        "Ni": "Ni",
        "Os": "Os",
        "Pb": "Pb",
        "Pm": "Pm",
        "Pr": "Pr",
        "Rb": "Rb_pv",
        "Re": "Re",
        "Rh": "Rh",
        "Ta": "Ta",
        "Tc": "Tc",
        "Ti": "Ti",
        "Tl": "Tl",
        "Yb": "Yb",
        "Zr": "Zr",
    }
)

PBE_GW_ELEMENT_MAPPINGS = {
    "Ac": "Ac",
    "Ag": "Ag_sv_GW",
    "Al": "Al_GW",
    "Ar": "Ar_GW",
    "As": "As_GW",
    "At": "At_d_GW",
    "Au": "Au_sv_GW",
    "B": "B_GW",
    "Ba": "Ba_sv_GW",
    "Be": "Be_sv_GW",
    "Bi": "Bi_d_GW",
    "Br": "Br_GW",
    "C": "C_GW",
    "Ca": "Ca_sv_GW",
    "Cd": "Cd_sv_GW",
    "Ce": "Ce_GW",
    "Cl": "Cl_GW",
    "Co": "Co_sv_GW",
    "Cr": "Cr_sv_GW",
    "Cs": "Cs_sv_GW",
    "Cu": "Cu_sv_GW",
    "Dy": "Dy_3",
    "Er": "Er_3",
    "Eu": "Eu",
    "F": "F_GW",
    "Fe": "Fe_sv_GW",
    "Ga": "Ga_d_GW",
    "Gd": "Gd",
    "Ge": "Ge_d_GW",
    "H": "H_GW",
    "He": "He_GW",
    "Hf": "Hf_sv_GW",
    "Hg": "Hg_sv_GW",
    "Ho": "Ho_3",
    "I": "I_GW",
    "In": "In_d_GW",
    "Ir": "Ir_sv_GW",
    "K": "K_sv_GW",
    "Kr": "Kr_GW",
    "La": "La_GW",
    "Li": "Li_sv_GW",
    "Lu": "Lu_3",
    "Mg": "Mg_sv_GW",
    "Mn": "Mn_sv_GW",
    "Mo": "Mo_sv_GW",
    "N": "N_GW",
    "Na": "Na_sv_GW",
    "Nb": "Nb_sv_GW",
    "Nd": "Nd_3",
    "Ne": "Ne_GW",
    "Ni": "Ni_sv_GW",
    "Np": "Np",
    "O": "O_GW",
    "Os": "Os_sv_GW",
    "P": "P_GW",
    "Pa": "Pa",
    "Pb": "Pb_d_GW",
    "Pd": "Pd_sv_GW",
    "Pm": "Pm_3",
    "Po": "Po_d_GW",
    "Pr": "Pr_3",
    "Pt": "Pt_sv_GW",
    "Pu": "Pu",
    "Rb": "Rb_sv_GW",
    "Re": "Re_sv_GW",
    "Rh": "Rh_sv_GW",
    "Rn": "Rn_d_GW",
    "Ru": "Ru_sv_GW",
    "S": "S_GW",
    "Sb": "Sb_d_GW",
    "Sc": "Sc_sv_GW",
    "Se": "Se_GW",
    "Si": "Si_GW",
    "Sm": "Sm_3",
    "Sn": "Sn_d_GW",
    "Sr": "Sr_sv_GW",
    "Ta": "Ta_sv_GW",
    "Tb": "Tb_3",
    "Tc": "Tc_sv_GW",
    "Te": "Te_GW",
    "Th": "Th",
    "Ti": "Ti_sv_GW",
    "Tl": "Tl_d_GW",
    "Tm": "Tm_3",
    "U": "U",
    "V": "V_sv_GW",
    "W": "W_sv_GW",
    "Xe": "Xe_GW",
    "Y": "Y_sv_GW",
    "Yb": "Yb_2",
    "Zn": "Zn_sv_GW",
    "Zr": "Zr_sv_GW",
}
