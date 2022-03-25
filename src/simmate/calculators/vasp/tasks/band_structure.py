# -*- coding: utf-8 -*-

import os

from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.symmetry.bandstructure import HighSymmKpath
from pymatgen.electronic_structure.plotter import BSPlotter

from simmate.calculators.vasp.inputs import Incar, Poscar, Potcar
from simmate.calculators.vasp.tasks.energy.materials_project import (
    MatProjStaticEnergy,
)


class MatProjBandStructure(MatProjStaticEnergy):
    """
    Calculates the band structure using Materials Project settings.

    Your stucture will be converted to the standardized-primitive unitcell so
    that the high-symmetry K-point path can be used.

    This is also a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which handles the preliminary relaxation and SCF
    energy calculation for you. This S3Task is only the final step of that workflow.

    See `vasp.workflows.band_structure`.
    """

    # The default settings to use for this calculation.
    # The key thing for band structures is that this follows a static energy
    # calculation. We use the CHGCAR from that previous calculation. We also
    # hold the charge density static during this calculation so this is a
    # non-selfconsistent (non-SCF) calculation.
    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        ICHARGE=11,
        ISMEAR=0,
        SIGMA=0.01,
    )

    # set the KptGrid or KptPath object
    # TODO: in the future, all functionality of this class will be available
    # by giving a KptPath class here.
    kpoints = None
    kpoints_line_density = 20

    # For band-structures, unit cells should be in the standardized format
    pre_standardize_structure = True

    def setup(self, structure, directory):
        """
        Writes input files for this calculation. This differs from the normal
        VaspTask setup because it converts the structure to the standard primative
        first and then writes a KPOINT file with using a highsym path.
        """

        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = self._get_clean_structure(structure)

        # write the poscar file
        Poscar.to_file(structure_cleaned, os.path.join(directory, "POSCAR"))

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**self.incar) + Incar(**self.incar_parallel_settings)
        incar.to_file(
            filename=os.path.join(directory, "INCAR"),
            structure=structure_cleaned,
        )

        ##############
        # we need to find the high-symmetry Kpt path. Note that all of this
        # functionality will be moved to the KptPath class and then extended to
        # vasp.inputs.kpoints class. Until those classes are ready, we just use
        # pymatgen here.
        sym_prec = self.incar.get("SYMPREC", 1e-5) if self.incar else 1e-5
        kpath = HighSymmKpath(structure_cleaned, symprec=sym_prec)
        frac_k_points, k_points_labels = kpath.get_kpoints(
            line_density=self.kpoints_line_density,
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
            self.functional,
            os.path.join(directory, "POTCAR"),
            self.potcar_mappings,
        )

    def _write_output_summary(self, directory, vasprun):
        """
        In addition to writing the normal VASP output summary, this also plots
        the bandstructure to "band_structure.png"
        """

        # run the normal output
        super()._write_output_summary(directory, vasprun)

        bs_plotter = BSPlotter(vasprun.get_band_structure(line_mode=True))
        plot = bs_plotter.get_plot()
        plot_filename = os.path.join(directory, "band_structure.png")
        plot.savefig(plot_filename)
