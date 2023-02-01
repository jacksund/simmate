# -*- coding: utf-8 -*-

from pymatgen.analysis.elasticity.strain import Strain, convert_strain_to_deformation

from simmate.toolkit import Structure
from simmate.toolkit.creators.vector import UniformlyDistributedVectors
from simmate.toolkit.transformations.base import Transformation


class LatticeStrain(Transformation):
    """
    Applies a large amount of strain to a lattice by shifting lattice vectors.
    The volume is then scaled back to the original volume. This is meant to
    break symmetries and allow a structure to relax.
    """

    #!!! should I mutate atomic sites too? USPEX is unclear if they do this
    # in addition to lattice strain. If so, I should look at the
    # CoordinateMutation transfomation class

    # strain is applied to the lattice and then the lattice is scaled back
    # to target volume
    # https://uspex-team.org/static/file/CPC-USPEX-2006.pdf

    # It looks like structure.apply_strain() is simply scaling each lattice
    # vector and not exactly what we'd like. Instead, I found
    # pymatgen.analysis.elasticity.strain module
    # https://pymatgen.org/pymatgen.analysis.elasticity.strain.html
    # Here, my understanding is that a strain matrix is not equivalent to a
    # deformation matrix. Therefore, I will create a Strain object, then convert
    # it Deformation object, then apply it to the structure

    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        fixed_volume: float,
        max_attempts=100,
    ):
        # after straining the lattice, we need to scale it to a fixed volume
        fixed_volume = fixed_volume

        # following along with USPEX paper, we need to first establish boundries
        # for the symmetric strain matrix
        # when generating components for this matrix, they randomly select
        # values between -1 and 1 in a guassian distribution
        component_generator = UniformlyDistributedVectors(min_value=-1, max_value=1)

        # first we need 6 strain matrix components
        components = component_generator.new_vector(size=6)

        # next we need to assemble the strain matrix using these components
        #!!! is there a better way to do this? I'm just using equation (3) in
        # the USPEX paper
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
        new_structure.scale_lattice(fixed_volume)

        return new_structure
