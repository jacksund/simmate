# -*- coding: utf-8 -*-

import numpy

from django.db import models

from simmate.database.structure import Structure
from simmate.database.calculation import Calculation

# Extra modules for plotting and visualization.
from plotly.subplots import make_subplots
import plotly.graph_objects as plotly_go
from django_pandas.io import read_frame


class IonicStepStructure(Structure):

    # You can view this table as a list of Structures that each have some extra
    # data attached to them from a calculation (such as energy) -- this is
    # specifically from a geometry relaxation.

    # Structure Relaxations are made up of a series of ionic steps -- where each
    # ionic step can be thought of as a single energy calculation. This yields
    # energy, forces, and lattice stress for a given structure. In many cases,
    # users won't need all of this data because they're only after the final
    # structure. However, all ionic steps are useful in the case of machine
    # learning where tons of data are needed. We therefore store these here.

    """Base Info"""

    # Note: we allow columns to be empty because the input structure for the
    # relaxation does not initially have this data below -- but we update it
    # later once the calculation runs.

    # Note: we assume that only converged data is being stored! So there is no
    # "converged_electronic" section here. ErrorHandlers and workups should
    # ensure this.

    # This is ionic step number for the given relaxation (starts counting from 0)
    ionic_step_number = models.IntegerField()

    # The final energy here includes corrections that VASP may have introduced
    energy = models.FloatField(blank=True, null=True)

    # A list of forces for each atomic site. So this is a list like...
    # [site1, site2, site3, ...] where site1=[force_x, force_y, force_z]
    site_forces = models.JSONField(blank=True, null=True)

    # This is 3x3 matrix that represents the stress on the structure lattice
    lattice_stress = models.JSONField(blank=True, null=True)

    """ Query-helper Info """
    # Takes the energy from above and converts it to per atom units
    energy_per_atom = models.FloatField(blank=True, null=True)

    # Takes the site forces and reports the vector norm for it.
    # See numpy.linalg.norm for how this is calculated.
    site_forces_norm = models.FloatField(blank=True, null=True)
    site_forces_norm_per_atom = models.FloatField(blank=True, null=True)

    # Takes the site forces and reports the vector norm for it.
    # # See numpy.linalg.norm for how this is calculated.
    lattice_stress_norm = models.FloatField(blank=True, null=True)
    lattice_stress_norm_per_atom = models.FloatField(blank=True, null=True)

    """ Relationships """
    # each of these will map to a Relaxation, so you should typically access this
    # data through that class. The exception to this is when you want all ionic
    # steps accross many relaxations for a machine learning input.
    # These relationship can be found via...
    #   relaxations
    #   relaxations_as_start
    #   relaxations_as_final

    """ Model Methods """
    # TODO: add a from_ionic_step method in the future when I have this class.

    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need
    # its own table.
    class Meta:
        abstract = True


class Relaxation(Calculation):

    """Base Info"""

    # OPTIMIZE
    # This data here is something we only get for the final structure, so it
    # may make sense to move this data into the IonicStepStructure table (and
    # allow null values for non-final steps). I instead keep this here because
    # I don't want columns above that are largely empty.
    # Note: all entries are optional because there is no guaruntee the calculation
    # finishes successfully
    band_gap = models.FloatField(blank=True, null=True)
    is_gap_direct = models.BooleanField(blank=True, null=True)
    energy_fermi = models.FloatField(blank=True, null=True)
    conduction_band_minimum = models.FloatField(blank=True, null=True)
    valence_band_maximum = models.FloatField(blank=True, null=True)

    """ Query-helper Info """

    # Volume Change (useful for checking if Pulay Stress may be significant)
    # We store this as a ratio relative to the starting structure
    #   (final - start) / start
    volume_change = models.FloatField(blank=True, null=True)

    """ Relationships """

    # !!! IMPORTANT !!!
    #
    # This class will typically map to specific tables so that relaxations
    # of different quality aren't all grouped together. Therefore, each subclass of
    # this should have relationships that look like this...
    #
    # structure_start = models.OneToOneField(
    #     IonicStepStructure,
    #     on_delete=models.CASCADE,
    #     related_name="relaxations_as_start",
    #     blank=True,
    #     null=True,
    # )
    # structure_final = models.OneToOneField(
    #     IonicStepStructure,
    #     on_delete=models.CASCADE,
    #     related_name="relaxations_as_final",
    #     blank=True,
    #     null=True,
    # )
    # structures = models.ForeignKey(
    #     IonicStepStructure,
    #     on_delete=models.CASCADE,
    #     related_name="relaxations",
    #     blank=True,
    #     null=True,
    # )
    #
    # Note that we allow these columns to be empty because we fill them up with
    # data after the Relaxation has been created.
    #
    # !!! IMPORTANT !!!

    """ Model Methods """

    def update_from_vasp_run(self, vasprun, corrections, IonicStepStructure_subclass):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.
        # The ionic_step_structure_subclass is where to save the structures and
        # is a subclass of IonicStepStructure.

        # The data is actually easier to access as a dictionary and everything
        # we need is stored under the "output" key
        data = vasprun.as_dict()["output"]

        # The only other data we need to grab is the list of structures. We can
        # pull the structure for each ionic step from the vasprun class directly.
        structures = vasprun.structures

        # Now let's iterate through the ionic steps and save these to the database.
        for number, (structure, ionic_step) in enumerate(
            zip(structures, data["ionic_steps"])
        ):
            # first pull all the data together and save it to the database
            structure = IonicStepStructure_subclass.from_pymatgen(
                structure=structure,
                ionic_step_number=number,
                energy=ionic_step["e_wo_entrp"],
                site_forces=ionic_step["forces"],
                lattice_stress=ionic_step["stress"],
                energy_per_atom=ionic_step["e_wo_entrp"] / structure.num_sites,
                site_forces_norm=numpy.linalg.norm(ionic_step["forces"]),
                site_forces_norm_per_atom=(
                    numpy.linalg.norm(ionic_step["forces"]) / structure.num_sites
                ),
                lattice_stress_norm=numpy.linalg.norm(ionic_step["stress"]),
                lattice_stress_norm_per_atom=(
                    numpy.linalg.norm(ionic_step["stress"]) / structure.num_sites
                ),
                relaxation=self,  # this links the structure to this relaxation
            )
            structure.save()

            # If this is the first structure, we want to link it as such
            if number == 0:
                self.structure_start_id = structure.id
            # and same for the final structure
            elif number == len(structures) - 1:
                self.structure_final_id = structure.id

        # calculate extra data for storing
        self.volume_change = (
            structures[-1].volume - structures[0].volume
        ) / structures[0].volume

        # There is also extra data for the final structure that we save directly
        # in the relaxation table
        self.band_gap = data["bandgap"]
        self.is_gap_direct = data["is_gap_direct"]
        self.energy_fermi = data["efermi"]
        self.conduction_band_minimum = data["cbm"]
        self.valence_band_maximum = data["vbm"]

        # lastly, we also want to save the corrections made
        self.corrections = corrections

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures = self.structures.order_by("ionic_step_number").all()
        structures_dataframe = read_frame(structures)

        # We will be making a figure that consists of 3 stacked subplots that
        # all share the x-axis of ionic_step_number
        figure = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
        )

        # Generate a plot for Energy (per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["energy_per_atom"],
            ),
            row=1,
            col=1,
        )

        # Generate a plot for Forces (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["site_forces_norm_per_atom"],
            ),
            row=2,
            col=1,
        )

        # Generate a plot for Stress (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["lattice_stress_norm_per_atom"],
            ),
            row=3,
            col=1,
        )

        # Now let's clean up some formatting and add the axes titles
        figure.update_layout(
            width=600,
            height=600,
            showlegend=False,
            xaxis3_title="Ionic Step (#)",
            yaxis_title="Energy (eV/atom)",
            yaxis2_title="Site Forces",
            yaxis3_title="Lattice Stress",
        )

        # we return the figure object for the user
        return figure

    def view_convergence_plot(self):
        import plotly.io as pio

        pio.renderers.default = "browser"

        figure = self.get_convergence_plot()
        figure.show()

    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need
    # its own table.
    class Meta:
        abstract = True
