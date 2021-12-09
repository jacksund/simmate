# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)

from plotly.subplots import make_subplots
import plotly.graph_objects as plotly_go


class IonicStep(Structure, Thermodynamics, Forces):

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

    # Note: we assume that only converged data is being stored! So there is no
    # "converged_electronic" section here. ErrorHandlers and workups should
    # ensure this.

    # This is ionic step number for the given relaxation. This starts counting from 0.
    ionic_step_number = table_column.IntegerField()

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

    @classmethod
    def from_pymatgen(
        cls,
        ionic_step_number,
        structure,
        energy,
        site_forces,
        lattice_stress,
        relaxation,  # gives the related object for the foreign key
        as_dict=False,
    ):
        # because this is a combination of tables, I need to build the data for
        # each and then feed all the results into this class

        # first grab the full dictionaries for each parent model
        thermo_data = Thermodynamics.from_base_data(
            structure,
            energy,
            as_dict=True,
        )
        forces_data = Forces.from_base_data(
            structure,
            site_forces,
            lattice_stress,
            as_dict=True,
        )
        structure_data = Structure.from_pymatgen(structure, as_dict=True)

        # Now feed all of this dictionarying into one larger one.
        all_data = dict(
            ionic_step_number=ionic_step_number,
            relaxation=relaxation,
            **structure_data,
            **thermo_data,
            **forces_data,
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)

    @classmethod
    def create_subclass_from_relaxation(cls, name, relaxation, module, **extra_columns):

        # All structures in this table come from relaxation calculations, where
        # there can be many structures (one for each ionic steps) linked to a
        # single relaxation. This means the start structure, end structure, and
        # those structure in-between are stored together here.
        # Therefore, there's just a simple column stating which relaxation it
        # belongs to.
        NewClass = cls.create_subclass(
            f"{name}IonicStep",
            relaxation=table_column.ForeignKey(
                relaxation,
                on_delete=table_column.CASCADE,
                related_name="structures",
            ),
            module=module,
            **extra_columns,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewClass

    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need
    # its own table.
    class Meta:
        abstract = True
        app_label = "local_calculations"


class Relaxation(Structure, Calculation):

    # WARNING: The Structure here is the source structure! If you want the final
    # structure, be sure to grab it from the structure_final attribute, where
    # it is saved as an IonicStep

    """Base Info"""

    # OPTIMIZE
    # This data here is something we only get for the final structure, so it
    # may make sense to move this data into the IonicStepStructure table (and
    # allow null values for non-final steps). I instead keep this here because
    # I don't want columns above that are largely empty.
    # Note: all entries are optional because there is no guaruntee the calculation
    # finishes successfully
    band_gap = table_column.FloatField(blank=True, null=True)
    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    energy_fermi = table_column.FloatField(blank=True, null=True)
    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    valence_band_maximum = table_column.FloatField(blank=True, null=True)

    """ Query-helper Info """

    # Volume Change (useful for checking if Pulay Stress may be significant)
    # We store this as a ratio relative to the starting structure
    #   (volume_final - volume_start) / volume_start
    volume_change = table_column.FloatField(blank=True, null=True)

    """ Relationships """

    # structure_start
    # structure_final
    # structures

    @classmethod
    def create_all_subclasses(cls, name, module, **extra_columns):

        # For convience, we add columns that point to the start and end structures
        NewRelaxationClass = cls.create_subclass(
            f"{name}Relaxation",
            structure_start=table_column.OneToOneField(
                f"{name}IonicStep",
                on_delete=table_column.CASCADE,
                related_name="relaxations_as_start",
                blank=True,
                null=True,
            ),
            structure_final=table_column.OneToOneField(
                f"{name}IonicStep",
                on_delete=table_column.CASCADE,
                related_name="relaxations_as_final",
                blank=True,
                null=True,
            ),
            module=module,
            **extra_columns,
        )

        NewIonicStepClass = IonicStep.create_subclass_from_relaxation(
            name,
            NewRelaxationClass,
            module=module,
            **extra_columns,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewRelaxationClass, NewIonicStepClass

    """ Model Methods """

    def update_from_vasp_run(self, vasprun, corrections, directory):
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
            # first pull all the data together and save it to the database. We
            # are saving this to an IonicStepStructure datatable. To access this
            # model, we look need to use "structures.model".
            structure = self.structures.model.from_pymatgen(
                number,
                structure,
                energy=ionic_step["e_wo_entrp"],
                site_forces=ionic_step["forces"],
                lattice_stress=ionic_step["stress"],
                relaxation=self,  # this links the structure to this relaxation
            )
            structure.save()

            # If this is the first structure, we want to link it as such
            if number == 0:
                self.structure_start_id = structure.id
            # and same for the final structure. Note, we can't use elif becuase
            # there's a chance the start/end structure are the same, which occurs
            # when the starting structure is found to be relaxed already.
            if number == len(structures) - 1:
                self.structure_final_id = structure.id
        # calculate extra data for storing
        self.volume_change = (
            structures[-1].volume - structures[0].volume
        ) / structures[0].volume

        # There is also extra data for the final structure that we save directly
        # in the relaxation table.  We use .get() in case the key isn't provided.
        self.band_gap = data.get("bandgap")
        self.is_gap_direct = data.get("is_gap_direct")
        self.energy_fermi = data.get("efermi")
        self.conduction_band_minimum = data.get("cbm")
        self.valence_band_maximum = data.get("vbm")

        # lastly, we also want to save the corrections made and directory it ran in
        self.corrections = corrections
        self.directory = directory

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.structures.order_by(
            "ionic_step_number"
        ).to_dataframe()

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
        app_label = "local_calculations"
