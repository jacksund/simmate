# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.static_energy.materials_project import (
    MatprojStaticEnergy,
)


class MatprojELF(MatprojStaticEnergy):
    """
    Runs a static energy calculation under settings from the Materials Project
    and also writes the electron localization function (to ELFCAR).
    """

    incar = MatprojStaticEnergy.incar.copy()
    incar.update(
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        # BUG: if NPAR conflicts with INCAR_parallel_settings config this
        # fails and tells the user to specify a setting
    )


# -----------------------------------------------------------------------------

# Below are old notes from a script I used to workup ELF. These might be useful
# if I want to update the workup method of this task. For now, no extra workup
# is done for this calculation as typically the ELFCAR is just used for
# visualization.

# -----------------------------------------------------------------------------

# # import the VASP results
# from pymatgen.io.vasp.outputs import Vasprun

# xmlReader = Vasprun(
#     filename="vasprun.xml",
#     parse_dos=True,
#     parse_eigen=True,
#     parse_projected_eigen=False,
#     parse_potcar_file=True,
#     exception_on_bad_xml=True,
# )


# # grab the info we want
# final_structure = xmlReader.structures[-1]  # or Structure.from_file('CONTCAR')
# final_energy = (
#     xmlReader.final_energy / final_structure.num_sites
# )  #!!! convert this to per_atom!
# converged = xmlReader.converged

# from pymatgen.io.vasp.outputs import Elfcar

# elfcar = Elfcar.from_file("ELFCAR")

# alphacar = elfcar.get_alpha()
# alphacar.write_file("ALPHACAR.vasp")

# from pymatgen.io.vasp.outputs import Chgcar

# chgcar = Chgcar.from_file("CHGCAR")

# # scale data of the Elfcar to the size of Chgcar using Kronecker product
# import numpy as np

# scale = [
#     int(c / e) for c, e in zip(chgcar.data["total"].shape, elfcar.data["total"].shape)
# ]
# elfcar_scaled = np.kron(elfcar.data["total"], np.ones(scale))
# from scipy.ndimage import gaussian_filter  #!!! This is for smoothing and optional

# elfcar_scaled = gaussian_filter(elfcar_scaled, sigma=0.75)
# # from scipy.linalg import kron
# # elfcar_scaled = kron(elfcar.data["total"], chgcar.data["total"])
# elfcar_scaled = Elfcar(elfcar.structure, {"total": elfcar_scaled})
# elfcar_scaled.write_file("ELFCAR_scaled.vasp")

# alphacar_scaled = elfcar_scaled.get_alpha()
# alphacar_scaled.write_file("ALPHACAR_scaled.vasp")

# # also write the crystal structure because it may differ from the input
# elfcar.structure.to(filename="primitive_structure.cif")

# # For 3d integrations:
# # https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.tplquad.html
# # def f(x,y,z):
# #     return chgcar.data['total'][0][1][2]
# # tplquad(f, 1, 2, lambda x: 2, lambda x: 3, lambda x, y: 0, lambda x, y: 1)
# # OR
# # https://stackoverflow.com/questions/47415122/calculate-the-volume-of-3d-plot


# import numpy as np
# import itertools


# def get_integrated_total(elfcar, ind, radius, nbins=1):
#     """
#     Get integrated difference of atom index ind up to radius. This can be
#     an extremely computationally intensive process, depending on how many
#     grid points are in the VolumetricData.
#     Args:
#         ind (int): Index of atom.
#         radius (float): Radius of integration.
#         nbins (int): Number of bins. Defaults to 1. This allows one to
#             obtain the charge integration up to a list of the cumulative
#             charge integration values for radii for [radius/nbins,
#             2 * radius/nbins, ....].
#     Returns:
#         Differential integrated charge as a np array of [[radius, value],
#         ...]. Format is for ease of plotting. E.g., plt.plot(data[:,0],
#         data[:,1])
#     """
#     struct = elfcar.structure
#     a = elfcar.dim
#     if (
#         ind not in elfcar._distance_matrix
#         or elfcar._distance_matrix[ind]["max_radius"] < radius
#     ):
#         coords = []
#         for (x, y, z) in itertools.product(*[list(range(i)) for i in a]):
#             coords.append([x / a[0], y / a[1], z / a[2]])
#         sites_dist = struct.lattice.get_points_in_sphere(
#             coords, struct[ind].coords, radius
#         )
#         elfcar._distance_matrix[ind] = {
#             "max_radius": radius,
#             "data": np.array(sites_dist),
#         }

#     data = elfcar._distance_matrix[ind]["data"]

#     # Use boolean indexing to find all charges within the desired distance.
#     inds = data[:, 1] <= radius
#     dists = data[inds, 1]
#     data_inds = np.rint(
#         np.mod(list(data[inds, 0]), 1) * np.tile(a, (len(dists), 1))
#     ).astype(int)
#     vals = [elfcar.data["total"][x, y, z] for x, y, z in data_inds]  #!!! diff to total

#     hist, edges = np.histogram(dists, bins=nbins, range=[0, radius], weights=vals)
#     data = np.zeros((nbins, 2))
#     data[:, 0] = edges[1:]
#     data[:, 1] = [sum(hist[0 : i + 1]) / elfcar.ngridpts for i in range(nbins)]
#     return data


# data = get_integrated_total(chgcar, ind=0, radius=2.5, nbins=100)

# import matplotlib.pyplot as plt

# plt.plot(data[:, 0], data[:, 1])
