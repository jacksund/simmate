# -*- coding: utf-8 -*-


from pymatgen.io.vasp.sets import DictSet

#!!! The warning that is raised here is because there is no YAML! It can be ignored
class MyCustomSet(DictSet):

    CONFIG = {
        "INCAR": {
            # Base Settings
            "NSW": 0,  # Max ionic steps (0 is static energy calc)
            "IVDW": 12,  # use Grimmes VDW correction
            "NELM": 100,  # Max SCF loops allowed
            "ISPIN": 2,  # run spin-polarized
            # Quality of Calc
            "PREC": "Accurate",  #
            "EDIFF": 1.0e-07,  # Break condition for SCF loop
            "EDIFFG": -1e-04,  # Break condition for ionic step loop # negative has different meaning!
            "ENCUT": 500,
            "ISIF": 3,  # Relax cell shape, volume, and atomic positions
            "ISMEAR": 0,  # Guassian smearing
            "SIGMA": 0.060,
            # Deciding which files to write
            "LCHARG": True,  # write CHGCAR
            "LWAVE": True,  # write WAVECAR
            "LELF": True,  # write ELFCAR
            # Parallel Options
            "NPAR": 1,  # Must be set if LELF is set to True
        },
        "KPOINTS": {"reciprocal_density": 50},
        "POTCAR_FUNCTIONAL": "PBE",
        "POTCAR": {
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
        },
    }

    def __init__(self, structure, **kwargs):
        """
        :param structure: Structure
        :param kwargs: Same as those supported by DictSet.
        """
        super().__init__(structure, MyCustomSet.CONFIG, **kwargs)
        self.kwargs = kwargs


# -----------------------------------------------------------------------------

print("Setting up...")
# load structure
from pymatgen.core.structure import Structure

structure = Structure.from_file("Y2C.cif")  #!!! NAME YOUR INPUT STRUCTURE FILE HERE
structure = structure.get_primitive_structure()

# write the vasp input files
MyCustomSet(structure).write_input(".")

# -----------------------------------------------------------------------------

print("Running vasp...")

# run vasp
import subprocess

subprocess.run(
    "module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out",
    shell=True,
)

# -----------------------------------------------------------------------------

print("Working up...")
# import the VASP results
from pymatgen.io.vasp.outputs import Vasprun

xmlReader = Vasprun(
    filename="vasprun.xml",
    parse_dos=True,
    parse_eigen=True,
    parse_projected_eigen=False,
    parse_potcar_file=True,
    exception_on_bad_xml=True,
)


# grab the info we want
final_structure = xmlReader.structures[-1]  # or Structure.from_file('CONTCAR')
final_energy = (
    xmlReader.final_energy / final_structure.num_sites
)  #!!! convert this to per_atom!
converged = xmlReader.converged

from pymatgen.io.vasp.outputs import Elfcar

elfcar = Elfcar.from_file("ELFCAR")

alphacar = elfcar.get_alpha()
alphacar.write_file("ALPHACAR.vasp")

from pymatgen.io.vasp.outputs import Chgcar

chgcar = Chgcar.from_file("CHGCAR")

# scale data of the Elfcar to the size of Chgcar using Kronecker product
import numpy as np

scale = [
    int(c / e) for c, e in zip(chgcar.data["total"].shape, elfcar.data["total"].shape)
]
elfcar_scaled = np.kron(elfcar.data["total"], np.ones(scale))
from scipy.ndimage import gaussian_filter  #!!! This is for smoothing and optional

elfcar_scaled = gaussian_filter(elfcar_scaled, sigma=0.75)
# from scipy.linalg import kron
# elfcar_scaled = kron(elfcar.data["total"], chgcar.data["total"])
elfcar_scaled = Elfcar(elfcar.structure, {"total": elfcar_scaled})
elfcar_scaled.write_file("ELFCAR_scaled.vasp")

alphacar_scaled = elfcar_scaled.get_alpha()
alphacar_scaled.write_file("ALPHACAR_scaled.vasp")

# also write the crystal structure because it may differ from the input
elfcar.structure.to(filename="primitive_structure.cif")

# For 3d integrations:
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.tplquad.html
# def f(x,y,z):
#     return chgcar.data['total'][0][1][2]
# tplquad(f, 1, 2, lambda x: 2, lambda x: 3, lambda x, y: 0, lambda x, y: 1)
# OR
# https://stackoverflow.com/questions/47415122/calculate-the-volume-of-3d-plot

# -----------------------------------------------------------------------------

raise NameError

import numpy as np
import itertools


def get_integrated_total(elfcar, ind, radius, nbins=1):
    """
    Get integrated difference of atom index ind up to radius. This can be
    an extremely computationally intensive process, depending on how many
    grid points are in the VolumetricData.
    Args:
        ind (int): Index of atom.
        radius (float): Radius of integration.
        nbins (int): Number of bins. Defaults to 1. This allows one to
            obtain the charge integration up to a list of the cumulative
            charge integration values for radii for [radius/nbins,
            2 * radius/nbins, ....].
    Returns:
        Differential integrated charge as a np array of [[radius, value],
        ...]. Format is for ease of plotting. E.g., plt.plot(data[:,0],
        data[:,1])
    """
    struct = elfcar.structure
    a = elfcar.dim
    if (
        ind not in elfcar._distance_matrix
        or elfcar._distance_matrix[ind]["max_radius"] < radius
    ):
        coords = []
        for (x, y, z) in itertools.product(*[list(range(i)) for i in a]):
            coords.append([x / a[0], y / a[1], z / a[2]])
        sites_dist = struct.lattice.get_points_in_sphere(
            coords, struct[ind].coords, radius
        )
        elfcar._distance_matrix[ind] = {
            "max_radius": radius,
            "data": np.array(sites_dist),
        }

    data = elfcar._distance_matrix[ind]["data"]

    # Use boolean indexing to find all charges within the desired distance.
    inds = data[:, 1] <= radius
    dists = data[inds, 1]
    data_inds = np.rint(
        np.mod(list(data[inds, 0]), 1) * np.tile(a, (len(dists), 1))
    ).astype(int)
    vals = [elfcar.data["total"][x, y, z] for x, y, z in data_inds]  #!!! diff to total

    hist, edges = np.histogram(dists, bins=nbins, range=[0, radius], weights=vals)
    data = np.zeros((nbins, 2))
    data[:, 0] = edges[1:]
    data[:, 1] = [sum(hist[0 : i + 1]) / elfcar.ngridpts for i in range(nbins)]
    return data


data = get_integrated_total(chgcar, ind=0, radius=2.5, nbins=100)

import matplotlib.pyplot as plt

plt.plot(data[:, 0], data[:, 1])
