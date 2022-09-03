# -*- coding: utf-8 -*-

from pathlib import Path

import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots
from pymatgen.io.vasp.outputs import Vasprun

from simmate.database.base_data_types import (
    Calculation,
    Forces,
    Structure,
    Thermodynamics,
    table_column,
)
from simmate.visualization.plotting import PlotlyFigure


class Dynamics(Structure, Calculation):
    """
    Holds results from a dynamics simulations -- often referred to as a molecular
    dynamics run.

    In addition to the attributes listed, you can also access all ionic steps
    of the run via the `structures` attribute. This attribute gives a list of
    `DynamicsIonicSteps`.
    """

    class Meta:
        app_label = "workflows"

    api_filters = dict(
        temperature_start=["range"],
        temperature_end=["range"],
        time_step=["range"],
        nsteps=["range"],
    )

    temperature_start = table_column.IntegerField(blank=True, null=True)
    """
    The starting tempertature of the simulation in Kelvin.
    """

    temperature_end = table_column.IntegerField(blank=True, null=True)
    """
    The ending tempertature of the simulation in Kelvin.
    """

    time_step = table_column.FloatField(blank=True, null=True)
    """
    The time in picoseconds for each step in the simulation.
    """

    nsteps = table_column.IntegerField(blank=True, null=True)
    """
    The total number of steps in the simulation. Note, this is the maximum cutoff
    steps set. In some cases, there may be fewer steps when the simulation is 
    stopped early.
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)
        self.write_simmulation_detail_plot(directory=directory)

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun):
        raise NotImplementedError(
            "Dynamics runs cannot currently be loaded from a dir/vasprun, so"
            "input parameters such as temperature and nsteps are not loaded. "
            "This feature is still under development"
        )
        # See Relaxation.from_vasp_run as a starting point

    def update_from_directory(self, directory: Path):

        # check if we have a VASP directory
        vasprun_filename = directory / "vasprun.xml"
        if not vasprun_filename.exists():
            # raise Exception(
            #     "Only VASP output directories are supported at the moment"
            # )
            return  # just exit

        from simmate.calculators.vasp.outputs import Vasprun

        vasprun = Vasprun.from_directory(directory)
        self.update_from_vasp_run(vasprun)

    def update_from_vasp_run(self, vasprun: Vasprun):
        """
        Given a Vasprun object from a finished dynamics run, this will update the
        Dynamics table entry and the corresponding DynamicsIonicStep entries.

        #### Parameters

        vasprun :
            The final Vasprun object from the dynamics run outputs.
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
            # are saving this to an DynamicsIonicStepStructure datatable. To access this
            # model, we look need to use "structures.model".
            structure = self.structures.model.from_toolkit(
                number=number,
                structure=structure,
                energy=ionic_step.get("e_wo_entrp", None),
                site_forces=ionic_step.get("forces", None),
                lattice_stress=ionic_step.get("stress", None),
                temperature=self._get_temperature_at_step(number),
                # simulation_time=number*self.time_step,
                dynamics_run=self,  # this links the structure to this dynamics run
            )
            structure.save()

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()

    def _get_temperature_at_step(self, step_number: int):
        return step_number * self._get_temperature_step_size() + self.temperature_start

    def _get_temperature_step_size(self):
        return (self.temperature_end - self.temperature_start) / self.nsteps


class DynamicsIonicStep(Structure, Thermodynamics, Forces):
    """
    Holds information for a single ionic step of a `Dynamics` entry.

    Each entry will map to a `Dynamics`, so you should typically access this
    data through that class. The exception to this is when you want all ionic
    steps accross many relaxations for a machine learning input.
    """

    class Meta:
        app_label = "workflows"

    archive_fields = ["number"]

    api_filters = dict(
        number=["range"],
        temperature=["range"],
    )

    number = table_column.IntegerField()
    """
    This is ionic step number for the given relaxation. This starts counting from 0.
    """

    temperature = table_column.FloatField(blank=True, null=True)
    """
    Expected temperature based on the temperature_start/end and nsteps. Note
    that in-practice some steps may not be at equilibrium temperatue. This could
    be the 1st 100 steps of a run or alternatively when the thermostat component
    is off-temperature.
    """

    dynamics_run = table_column.ForeignKey(
        Dynamics,
        on_delete=table_column.CASCADE,
        related_name="structures",
    )
    """
    All structures in this table come from dynamics run calculations, where
    there can be many structures (one for each ionic step) linked to a
    single run. This means the start structure, end structure, and
    those structure in-between are stored together here.
    Therefore, there's just a simple column stating which relaxation it
    belongs to.
    """

    # TODO:
    # simulation_time = table_column.FloatField(blank=True, null=True)
    # """
    # The total simulation time up to this ionic step (in picoseconds). This is
    # just "number*time_step", but we store this in the database for easy access.
    # """

    # TODO: Additional options from Vasprun.as_dict to consider adding
    # e_0_energy
    # e_fr_energy
    # kinetic
    # lattice kinetic
    # nosekinetic
    # nosepot


class SimmulationDetail(PlotlyFigure):
    def get_plot(result: Dynamics):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = result.structures.order_by("number").to_dataframe()

        # We will be making a figure that consists of 3 stacked subplots that
        # all share the x-axis of ionic_step_number
        figure = make_subplots(
            rows=4,
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

        # Generate a plot for Stress (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["number"],
                y=structures_dataframe["temperature"],
            ),
            row=4,
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
            yaxis4_title="Temperature (K)",
        )

        return figure


# register all plotting methods to the database table
for _plot in [SimmulationDetail]:
    _plot.register_to_class(Dynamics)
