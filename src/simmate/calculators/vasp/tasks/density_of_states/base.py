# -*- coding: utf-8 -*-

import os

from pymatgen.electronic_structure.plotter import DosPlotter

from simmate.calculators.vasp.tasks.static_energy.materials_project import (
    MatprojStaticEnergy,
)


class VaspDensityOfStates(MatprojStaticEnergy):
    """
    A base class for density of states (DOS) calculations. This is not meant
    to be used directly but instead should be inherited from.

    This is also a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.
    """

    required_files = MatprojStaticEnergy.required_files + ["CHGCAR"]

    @staticmethod
    def _write_output_summary(directory, vasprun):
        """
        In addition to writing the normal VASP output summary, this also plots
        the DOS to "density_of_states.png"
        """

        # run the normal output
        MatprojStaticEnergy._write_output_summary(directory, vasprun)

        # and then generate a DOS plot
        plotter = DosPlotter()

        # Add the total density of States
        plotter.add_dos("Total DOS", vasprun.complete_dos)

        # add element-projected density of states
        plotter.add_dos_dict(vasprun.complete_dos.get_element_dos())

        # If I want plots for individual orbitals
        # for site in vasprun.final_structure:
        #     spd_dos = vasprun.complete_dos.get_site_spd_dos(site)
        #     plotter.add_dos_dict(spd_dos)

        # NOTE: get_dos_dict may be useful in the future

        plot = plotter.get_plot()
        plot_filename = os.path.join(directory, "density_of_states.png")
        plot.savefig(plot_filename)
