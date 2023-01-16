# -*- coding: utf-8 -*-


import itertools

import numpy
import pandas
from matminer.featurizers.structure.rdf import PartialRadialDistributionFunction
from scipy.ndimage import gaussian_filter1d, zoom
from scipy.stats import linregress

from simmate.toolkit import Structure

# TODO: add other elements
CROSS_SECTIONS_CONSTANTS = {"Al": 5.704193e-2, "O": 2.029453e-2}


class RdfSlab(Structure):
    """
    Adds a few extra methods to Structures that are assumed to be 2D slabs.

    The slab must be orthogonal to the z axis.
    """

    # Take a look at pymatgen's Slab module. This could help generate input
    # structures or add extra methods to the structure class. I bet down the line
    # that you'll end up with a Slab class of your own
    # https://pymatgen.org/pymatgen.core.surface.html#pymatgen.core.surface.Slab

    # all features of the Structure class will be kept
    # But do you always want a slab input...? Will your program be capable of
    # running bulk structures?

    # -------------------------------------------------------------------------
    # Methods for quickly accessing slab properties
    # -------------------------------------------------------------------------

    @property
    def thickness_z(self):
        max_z = max([coords[2] for coords in self.cart_coords])
        min_z = min([coords[2] for coords in self.cart_coords])
        thickness = max_z - min_z
        # center = (max_z + min_z) / 2  # is this ever used?
        return thickness

    @property
    def slab_volume(self):

        # we need volume of our slab for the calculation of g(r)

        # BUG: assumes c vector along z axis
        if self.lattice.matrix[2][0] or self.lattice.matrix[2][1]:
            raise Exception(
                "This method requires the c lattice vector to be "
                "directly parallel to the z axis"
            )

        a = self.lattice.matrix[0]
        b = self.lattice.matrix[1]
        c = [0, 0, self.thickness_z]
        volume = numpy.dot(numpy.cross(a, b), c)

        return volume

    @property
    def slab_density(self):
        return self.composition.weight / self.slab_volume

    @property
    def element_pairs(self):

        elements = self.symbol_set
        return list(itertools.combinations_with_replacement(elements, 2))

    def move_index(self, move_index):
        self.move_index = move_index

    def update_xyz(self, move_index, new_position, move_vector, max_step, old_position):

        """update position"""

        # old_position = copy.deepcopy(list(self.xyz_df['df_x'].loc[move_index][0:4]))

        print("before df update")
        print(self.xyz_df["df_x"].loc[move_index])

        for d in self.xyz_df.values():
            d.at[move_index, "x"] = new_position[0]
            d.at[move_index, "y"] = new_position[1]
            d.at[move_index, "z"] = new_position[2]

        print("after df update")
        print(self.xyz_df["df_x"].loc[move_index])

        """ sort df_x, df_y, df_z """

        df_x_original = self.xyz_df["df_x"].at[move_index, "x"]
        print(df_x_original)

        for i, df_name in enumerate(["df_x", "df_y", "df_z"]):
            df = self.xyz_df[df_name]
            axis = df_name[-1]
            df.sort_values(axis, inplace=True)

        if self.xyz_df["df_x"].at[move_index, "x"] != df_x_original:
            breakpoint()

        # for df_x, see if we increased/decreased x value.
        # sorted = False
        # while False:
        #     if we increased, check the neighboring value below
        #     if we decreased, check the neighboring value above.
        #     if value is < > ... neighbor then move.
        #     else:  sorted = True

    # -------------------------------------------------------------------------
    # Methods/attributes for generating and caching pRDFs
    # -------------------------------------------------------------------------

    ##################
    # We need to now insert our pymatgen code that gets a fast RDF.
    ##################

    # Pymatgen-analysis-diffusion RDF utilities
    # https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/aimd/rdf.py
    #

    """
    Do we want Gaussian smearing?
    Do we divide by the number density rho to get g(r)?
    
    Some notes on the pymatgen.analysis.diffusion.aimd.rdf.RadialDistributionFunction
    The property .raw_rdf gives no smearing whereas .rdf does.
    Both .raw_rdf and .rdf  have the same integrated area.
    Both .raw_rdf and .rdf divide by rho (the number density).
    Both .raw_rdf and .rdf are single-counting rather than double counting.
    
    As implemented, we need to ensure the separation between slabs in z is
    greater than the RDF r_max.  Otherwise we accidentally count atoms in the
    vertical direction.
    
    We should therefore have a validator check that z_separation > r_max at the
    start of a calculation.
    
    How do we quickly generate a list of indices of just one atom type?
    Here, we call this atom_list_1, atom_list_2
    
    """

    @property
    def weightings(self):
        normalization = 0
        for el1, el2 in self.element_pairs:
            b1 = CROSS_SECTIONS_CONSTANTS[el1]
            b2 = CROSS_SECTIONS_CONSTANTS[el2]
            m1 = self.composition.get_atomic_fraction(el1)
            m2 = self.composition.get_atomic_fraction(el2)
            normalization += m1 * b1 * m2 * b2
        weightings = {}
        for pair in self.element_pairs:
            el1, el2 = pair
            b1 = CROSS_SECTIONS_CONSTANTS[el1]
            b2 = CROSS_SECTIONS_CONSTANTS[el2]
            m1 = self.composition.get_atomic_fraction(el1)
            m2 = self.composition.get_atomic_fraction(el2)
            numerator = m1 * b1 * m2 * b2
            weighting = numerator / normalization
            weightings[pair] = weighting
        return weightings

    @property
    def partial_rdfs(self):

        # OPTIMIZE: consider caching the creation/fitting of this class because
        # it never changes. (i.e move it to a separate method and use @cached_property)
        prdf_maker = PartialRadialDistributionFunction(
            cutoff=10,
            bin_size=0.04,
        )
        prdf_maker.fit([self])

        # Above this line potentially cache
        # Below this line the function is slow.  Wasting time grabbing elements.

        # Grab the partial RDFs
        bins, prdf_dict = prdf_maker.compute_prdf(self)

        # replace the rdfs with smoothed rdfs
        # this part is optional / needs tweaking to optimize

        for pair, rdf in prdf_dict.items():
            rdf_normalized = rdf * self.slab_volume / self.composition[pair[1]]
            rdf_smoothed = gaussian_filter1d(rdf_normalized, sigma=1)
            prdf_dict[pair] = rdf_smoothed

        return prdf_dict

    @property
    def full_pdf_g(self):

        rdfs_dict = self.partial_rdfs
        weighting_dict = self.weightings

        # cutoff=10, bin_size=0.04 is hardcoded above --> array size will
        # always be 250.
        g = numpy.zeros(250)  # Why was numpy.double used before...?
        for pair in self.element_pairs:
            rdf = rdfs_dict[pair]
            weight = weighting_dict[pair]
            g += rdf * weight

        return g

    @property
    def full_pdf_G(self):

        # cutoff=10, bin_size=0.04 is hardcoded above --> array size will
        # always be 250. This info is also the "bins" variable in the
        # partial_rdfs method -- which we didn't save earlier
        r = numpy.arange(0, 10, 0.04)

        g = self.full_pdf_g
        rho = self.num_sites / self.volume  # CHANGE TO SLAB VOL WHEN NEEDED
        G = 4 * numpy.pi * rho * r * (g - 1)
        return G

    # -------------------------------------------------------------------------
    # Methods for comparing to experiment
    # -------------------------------------------------------------------------

    # These values are empty until load_experimental_from_file is called
    r_experimental = None
    G_experimental = None

    def load_experimental_from_file(self, file_name: str):
        data = pandas.read_csv(file_name)

        # save as attribute so we don't need to reload later
        self.r_experimental = data.r.values
        self.G_experimental = data.gr.values

    @property
    def prdf_error(self):

        if self.r_experimental is None or self.G_experimental is None:
            raise Exception("Please call load_experimental_from_file first")

        exp = self.G_experimental
        calc = self.full_pdf_G

        # we need to scale the calc pdf to be the same size (r) and same number
        # of bins (number of x values). Other option here to ensure the bin
        # size of the calc matches the experimental by default.
        # This code block is from...
        # https://stackoverflow.com/questions/55186867/
        current_size = len(calc)
        target_size = len(exp)
        zoom_factor = target_size / current_size
        calc_scaled = zoom(calc, zoom_factor)

        # do linear regression of experiment vs. calculated and grab the
        # standard error
        slope, intercept, rvalue, pvalue, stderr = linregress(
            exp,
            calc_scaled,
        )

        return stderr

    def _init_xyz_df(structure):
        import pandas as pd

        data = []
        for i, site in enumerate(structure.sites):
            temp = [
                site.coords[0],
                site.coords[1],
                site.coords[2],
                site.species_string,
            ]
            data.append(temp)
        labels = ["x", "y", "z", "el"]

        df = pd.DataFrame(data, columns=labels)

        df_x = df.copy().sort_values("x")
        df_y = df.copy().sort_values("y")
        df_z = df.copy().sort_values("z")

        return {"df_x": df_x, "df_y": df_y, "df_z": df_z}
