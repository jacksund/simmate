# -*- coding: utf-8 -*-

from pymatgen.analysis.elasticity.strain import Strain, convert_strain_to_deformation

from simmate.toolkit.transformations.base import Transformation
from simmate.toolkit.creators.vector import UniformlyDistributedVectors


class LatticeStrain(Transformation):

    #!!! should I mutate atomic sites too? USPEX is unclear if they do this in addition to lattice strain
    #!!! if I decide to do this, look at CoordinateMutation class below

    # strain is applied to the lattice and then the lattice is scaled back to target volume
    # https://uspex-team.org/static/file/CPC-USPEX-2006.pdf

    # It looks like structure.apply_strain() is simply scaling each lattice vector and not exactly what we'd like
    # Instead, I found pymatgen.analysis.elasticity.strain module
    # https://pymatgen.org/pymatgen.analysis.elasticity.strain.html
    # Here, my understanding is that a strain matrix is not equivalent to a deformation matrix
    # therefore, I will create a Strain object, then convert it Deformation object, then apply it to the structure

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(self, fixed_volume):

        # after straining the lattice, we need to scale it to a fixed volume
        self.fixed_volume = fixed_volume

        # following along with USPEX paper, we need to first establish boundries for the symmetric strain matrix
        # when generating components for this matrix, they randomly select values between -1 and 1 in a guassian distribution
        self.component_generator = UniformlyDistributedVectors(
            min_value=-1, max_value=1
        )

    def apply_transformation(self, structure, max_attempts=100):

        # first we need 6 strain matrix components
        components = self.component_generator.new_vector(size=6)

        # next we need to assemble the strain matrix using these components
        #!!! is there a better way to do this? I'm just using equation (3) in the USPEX paper
        strain_matrix = [
            [1 + components[0], components[5] / 2, components[4] / 2],
            [components[5] / 2, 1 + components[1], components[3] / 2],
            [components[4] / 2, components[3] / 2, 1 + components[2]],
        ]

        # now let's switch to pymatgen functionality

        # first make the Strain object
        strain = Strain(strain_matrix)

        # now convert it to a deformation object
        #!!! do I want the shape to be 'upper' or 'symmetric'??
        deformation = convert_strain_to_deformation(strain, shape="symmetric")

        # deform the structure
        new_structure = deformation.apply_to_structure(structure)

        # scale the lattice volume back to a fixed value
        new_structure.scale_lattice(self.fixed_volume)

        return new_structure
