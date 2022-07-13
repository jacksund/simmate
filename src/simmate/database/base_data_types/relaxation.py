# -*- coding: utf-8 -*-

"""
Structure Relaxations are made up of a series of ionic steps -- where each
ionic step can be thought of as a single energy calculation. This yields
energy, forces, and lattice stress for a given structure. In many cases,
users won't need all of this data because they're only after the final
structure. However, all ionic steps are useful in the case of confirming 
convergence as well as machine learning applications. We therefore store these
here.

This module helps you create tables to results from structure relaxations
(aka geometry optimizations). This will store all ionic steps and the forces/stress
associated with each step.

When creating new tables for Relaxations, you should use the `Relaxation.create_subclasses` method, which helps remove all the 
boilerplate code needed. For Django users, it may be tricky to understand what's
happening behind the scenes, so here's an example:
    
These two lines...

``` python 
from simmate.database.base_data_types import Relaxation

ExampleRelaxation, ExampleIonicStep = Relaxation.create_subclasses(
    "Example",
    module=__name__,
)
```

... do exactly the same thing as all of these lines...

``` python
from simmate.database.base_data_types import table_column
from simmate.database.base_data_types import IonicStep, Relaxation

class ExampleIonicStep(IonicStep):
    relaxation = table_column.ForeignKey(
        "ExampleRelaxation",  # in quotes becuase this is defined below
        on_delete=table_column.CASCADE,
        related_name="structures",
    )

class ExampleRelaxation(Relaxation):
    structure_start = table_column.OneToOneField(
        ExampleIonicStep,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_start",
        blank=True,
        null=True,
    )
    structure_final = table_column.OneToOneField(
        ExampleIonicStep,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_final",
        blank=True,
        null=True,
    )
```

Note there are two tables involved. One stores all of the ionic steps, and the
other connects all ionic steps to a specific calculation and result.

"""

import os

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)

from plotly.subplots import make_subplots
import plotly.graph_objects as plotly_go

from typing import List
from pymatgen.io.vasp.outputs import Vasprun


class Relaxation(Structure, Thermodynamics, Calculation):
    """
    This table holds all data from a structure relaxation and also links to
    IonicStep table which holds all of the structure/energy/forces for each
    ionic step.

    WARNING: The Structure stored in this table here is the source structure
    until the calculation completes. After completed, the structure will
    be updated to the final structure. If you wish to ensure you're accessing
    the correct structure, use the `structure_final` attribute, which gives
    the final IonicStep.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    base_info = (
        [
            "band_gap",
            "is_gap_direct",
            "energy_fermi",
            "conduction_band_minimum",
            "valence_band_maximum",
        ]
        + Structure.base_info
        + Calculation.base_info
    )

    # OPTIMIZE: should I include this electronic data?
    # This data here is something we only get for the final structure, so it
    # may make sense to move this data into the IonicStepStructure table (and
    # allow null values for non-final steps). I instead keep this here because
    # I don't want columns above that are largely empty.
    # Note: all entries are optional because there is no guaruntee the calculation
    # finishes successfully

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    """
    Whether the band gap is direct or indirect.
    """

    energy_fermi = table_column.FloatField(blank=True, null=True)
    """
    The Fermi energy in eV.
    """

    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    """
    The conduction band minimum in eV.
    """

    valence_band_maximum = table_column.FloatField(blank=True, null=True)
    """
    The valence band maximum in eV.
    """

    volume_change = table_column.FloatField(blank=True, null=True)
    """
    The percent volume change during the relaxation. This is useful for checking
    if Pulay Stress may be significant or if the structure was highly unreasonable.
    We store this as a ratio relative to the starting structure:
    ```
    (volume_final - volume_start) / volume_start
    ```
    """

    """ Relationships """
    # structure_start --> points to first (0) IonicStep
    # structure_final --> points to final IonicStep
    # structures --> gives list of all IonicSteps

    @classmethod
    def create_subclasses(cls, name: str, module: str, **extra_columns):
        """
        Dynamically creates a subclass of Relaxation as well as a separate IonicStep
        table for it. These tables are linked together.

        Example use:

        ``` python
        from simmate.database.base_data_types import Relaxation

        ExampleRelaxation, ExampleIonicStep = Relaxation.create_subclasses(
            "Example",
            module=__name__,
        )
        ```

        #### Parameters

        - `name` :
            The prefix name of the subclasses that are output. "Relaxation" and
            "IonicStep" will be attached to the end of this prefix.
        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.
        - `**extra_columns` :
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        #### Returns

        - `NewRelaxationClass` :
            A subclass of Relaxation.
        - `NewIonicStepClass`:
            A subclass of IonicStep.

        """

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

    @classmethod
    def from_directory(cls, directory: str):
        # I assume the directory is from a vasp calculation, but I need to update
        # this when I begin adding new calculators.
        vasprun_filename = os.path.join(directory, "vasprun.xml")
        vasprun = Vasprun(vasprun_filename)
        return cls.from_vasp_run(vasprun)

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun):

        # Make the relaxation entry. Note we need to save this to the database
        # in order to link/save the ionic steps below. We save the structure
        # as the final one in the calculation.
        # Note, the information does not matter at this point because it will be
        # populated below
        relaxation = cls.from_toolkit(structure=vasprun.structures[-1])
        # TODO: need to pull prefect_flow_run_id from metadata file.

        # Now we have the relaxation data all loaded and can save it to the database
        relaxation.save()

        # Save the rest of the results using the update method from this class
        relaxation.update_from_vasp_run(
            vasprun=vasprun,
            corrections=[],
            directory=None,
        )
        # TODO: load corrections/directory from the metadata and corrections files.

        return relaxation

    def update_from_vasp_run(
        self,
        vasprun: Vasprun,
        corrections: List,
        directory: str,
    ):
        """
        Given a Vasprun object from a finished relaxation, this will update the
        Relaxation table entry and the corresponding IonicStep entries.

        #### Parameters

        vasprun :
            The final Vasprun object from the relaxation outputs.
        corrections :
            List of errors and corrections applied to during the relaxation.
        directory :
            name of the directory that relaxation was ran in. This is only used
            to reference the archive file if it's ever needed again.
        """

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
            structure = self.structures.model.from_toolkit(
                number=number,
                structure=structure,
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

        # update our relaxation entry with new data
        self.update_from_toolkit(
            # use the final ionic setup for the structure and energy
            structure=structures[-1],
            energy=data["ionic_steps"][-1]["e_wo_entrp"],
            # calculate extra data for storing
            volume_change=structures[-1].volume
            - structures[0].volume / structures[0].volume,
            # There is also extra data for the final structure that we save directly
            # in the relaxation table.  We use .get() in case the key isn't provided.
            band_gap=data.get("bandgap"),
            is_gap_direct=data.get("is_gap_direct"),
            energy_fermi=data.get("efermi"),
            conduction_band_minimum=data.get("cbm"),
            valence_band_maximum=data.get("vbm"),
            # lastly, we also want to save the corrections made and directory it ran in
            corrections=corrections,
            directory=directory,
        )

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.structures.order_by("number").to_dataframe()

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
                x=structures_dataframe["number"],
                y=structures_dataframe["energy_per_atom"],
            ),
            row=1,
            col=1,
        )

        # Generate a plot for Forces (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["number"],
                y=structures_dataframe["site_forces_norm_per_atom"],
            ),
            row=2,
            col=1,
        )

        # Generate a plot for Stress (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["number"],
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
        figure = self.get_convergence_plot()
        figure.show(renderer="browser")

    def get_convergence_plot_html(self):
        # Make the convergence figure and convert it to an html div
        figure_convergence = self.get_convergence_plot()
        figure_convergence_html = figure_convergence.to_html(
            full_html=False,
            include_plotlyjs=False,
        )
        return figure_convergence_html


class IonicStep(Structure, Thermodynamics, Forces):
    """
    This database table that holds the data for each ionic step of a relaxation.

    An ionic step can be viewed as a static energy calculation, but we keep these
    results separate because:

        1. Pulay stress can make these energies/forces inaccurate
        2. These results each have an associated Relaxation and ionic step number

    You will likely never access this table directly. Instead, data is better
    accessed through the `structures` attribute on appropiate Relaxation table.

    For example:

    ``` python
    from simmate.database import connect
    from simmate.database.workflow_results import MITRelaxation

    # grab your desired relaxation
    relax = MITRelaxation.objects.get(id=1)

    # grab the associated ionic steps
    ionic_steps = relax.structures.all()
    ```

    Note: we assume that only converged data is being stored! So there is no
    "converged_electronic" column here. ErrorHandlers and workups should
    ensure convergence.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    base_info = (
        ["number"] + Structure.base_info + Thermodynamics.base_info + Forces.base_info
    )

    number = table_column.IntegerField()
    """
    The ionic step number within the relaxation. This starts counting from 0.
    """

    """ Relationships """
    # each of these will map to a Relaxation, so you should typically access this
    # data through that class. The exception to this is when you want all ionic
    # steps accross many relaxations for a machine learning input.
    # These relationship can be found via...
    #   relaxations
    #   relaxations_as_start
    #   relaxations_as_final

    @classmethod
    def create_subclass_from_relaxation(
        cls,
        name: str,
        relaxation: Relaxation,
        module: str,
        **extra_columns,
    ):
        """
        Dynamically creates a subclass of IonicStep and links it to the Relaxation
        table.

        This method should NOT be called directly because it is instead used by
        `Relaxation.create_subclasses`.

        #### Parameters

        - `name` :
            Name of the subclass that is output.
        - `relaxation` :
            Relaxation table that these ionic steps should be associated with.
        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.
        - `**extra_columns` :
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        Returns
        -------
        - `NewClass` :
            A subclass of IonicStep.

        """

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
