# -*- coding: utf-8 -*-

import os

from pymatgen.electronic_structure.plotter import DosPlotter

from simmate.calculators.vasp.tasks.energy.materials_project import (
    MatProjStaticEnergy,
)


class MatProjDensityOfStates(MatProjStaticEnergy):
    """
    Calculates the density of states using Materials Project settings.

    This is a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which handles the preliminary relaxation and SCF
    energy calculation for you. This S3Task is only the final step of that workflow.

    See `vasp.workflows.density_of_states`.
    """

    # Settings are based off of pymatgen's NonSCFSet in uniform mode
    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        ICHARGE=11,
        ISYM=2,
        NEDOS=2001,
    )
    incar.pop("MAGMOM__smart_magmom")

    def _write_output_summary(self, directory, vasprun):
        """
        In addition to writing the normal VASP output summary, this also plots
        the DOS to "density_of_states.png"
        """

        # run the normal output
        super()._write_output_summary(directory, vasprun)

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
