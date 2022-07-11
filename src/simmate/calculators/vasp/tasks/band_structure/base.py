# -*- coding: utf-8 -*-

import os

from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.symmetry.bandstructure import HighSymmKpath
from pymatgen.electronic_structure.plotter import BSPlotter

from simmate.calculators.vasp.inputs import Incar, Poscar, Potcar
from simmate.calculators.vasp.tasks.static_energy.materials_project import (
    MatprojStaticEnergy,
)


class VaspBandStructure(MatprojStaticEnergy):
    """
    A base class for band structure calculations. This is not meant
    to be used directly but instead should be inherited from.

    Your stucture will be converted to the standardized-primitive unitcell so
    that the high-symmetry K-point path can be used.

    This is also a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.
    """

    required_files = MatprojStaticEnergy.required_files + ["CHGCAR"]

    # set the KptGrid or KptPath object
    # TODO: in the future, all functionality of this class will be available
    # by giving a KptPath class here.
    kpoints = None
    kpoints_line_density = 20
    """
    Density of k-points to use along high-symmetry lines
    """

    @classmethod
    def setup(cls, directory, structure, **kwargs):
        """
        Writes input files for this calculation. This differs from the normal
        VaspTask setup because it converts the structure to the standard primative
        first and then writes a KPOINT file with using a highsym path.
        """

        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        # write the poscar file
        Poscar.to_file(structure_cleaned, os.path.join(directory, "POSCAR"))

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**cls.incar) + Incar(**cls.incar_parallel_settings)
        incar.to_file(
            filename=os.path.join(directory, "INCAR"),
            structure=structure_cleaned,
        )

        ##############
        # we need to find the high-symmetry Kpt path. Note that all of this
        # functionality will be moved to the KptPath class and then extended to
        # vasp.inputs.kpoints class. Until those classes are ready, we just use
        # pymatgen here.
        sym_prec = cls.incar.get("SYMPREC", 1e-5) if cls.incar else 1e-5
        kpath = HighSymmKpath(structure_cleaned, symprec=sym_prec)
        frac_k_points, k_points_labels = kpath.get_kpoints(
            line_density=cls.kpoints_line_density,
            coords_are_cartesian=False,
        )
        kpoints = Kpoints(
            comment="Non SCF run along symmetry lines",
            style=Kpoints.supported_modes.Reciprocal,
            num_kpts=len(frac_k_points),
            kpts=frac_k_points,
            labels=k_points_labels,
            kpts_weights=[1] * len(frac_k_points),
        )
        kpoints.write_file(os.path.join(directory, "KPOINTS"))
        ##############

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure_cleaned.composition.elements,
            cls.functional,
            os.path.join(directory, "POTCAR"),
            cls.potcar_mappings,
        )

    @staticmethod
    def _write_output_summary(directory, vasprun):
        """
        In addition to writing the normal VASP output summary, this also plots
        the bandstructure to "band_structure.png"
        """

        # run the normal output
        MatprojStaticEnergy._write_output_summary(directory, vasprun)

        bs_plotter = BSPlotter(vasprun.get_band_structure(line_mode=True))
        plot = bs_plotter.get_plot()
        plot_filename = os.path.join(directory, "band_structure.png")
        plot.savefig(plot_filename)
