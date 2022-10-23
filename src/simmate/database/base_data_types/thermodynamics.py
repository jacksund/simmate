# -*- coding: utf-8 -*-

import logging
import warnings

from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.toolkit import Structure as ToolkitStructure
from simmate.utilities import get_chemical_subsystems
from simmate.visualization.plotting import PlotlyFigure

# BUG: This prints a tqdm error so we silence it here.
with warnings.catch_warnings(record=True):
    from pymatgen.analysis.phase_diagram import PDEntry, PDPlotter, PhaseDiagram


class Thermodynamics(DatabaseTable):
    class Meta:
        abstract = True

    archive_fields = ["energy"]

    api_filters = dict(
        energy=["range"],
        energy_per_atom=["range"],
        energy_above_hull=["range"],
        is_stable=["exact"],
        formation_energy=["range"],
        formation_energy_per_atom=["range"],
    )

    energy = table_column.FloatField(blank=True, null=True)
    """
    The calculated total energy. Units are in eV.
    """

    energy_per_atom = table_column.FloatField(blank=True, null=True)
    """
    The `energy` divided by `nsites`. Units are in eV.
    """

    # TODO: These columns below should be updated on a schedule. I'd run
    # a prefect flow every night that makes sure all values are up to date.

    energy_above_hull = table_column.FloatField(blank=True, null=True)
    """
    The hull energy (aka "stability") of this structure compared to all other
    structures in this database table. Units are in eV.
    """

    is_stable = table_column.BooleanField(blank=True, null=True)
    """
    Whether `energy_above_hull` is 0 -- if so, this is considered stable.
    """

    decomposes_to = table_column.JSONField(blank=True, null=True)
    """
    If `energy_above_hull` is above 0, these are the compositions that the 
    structure will decompose to (e.g. ["Y2C", "C", "YF3"])
    """

    formation_energy = table_column.FloatField(blank=True, null=True)
    """
    The formation energy of the structure relative to all other
    structures in this database table. Units are in eV.
    """

    formation_energy_per_atom = table_column.FloatField(blank=True, null=True)
    """
    The `formation_energy` divided by `nsites`.
    """

    # Other fields to consider
    # equilibrium_reaction_energy_per_atom
    # energy_uncertainy_per_atom
    # energy_per_atom_uncorrected
    # decompose_amount (to each decomp type)

    """ Properties """
    # These are some extra fields to consider adding
    # energy_type = ... (DFT, machine-learned, LJ, etc.)
    # calc_types = (list) https://github.com/materialsproject/emmet/blob/main/emmet-core/emmet/core/vasp/calc_types/utils.py
    # psudeopotential
    #     functional(PBE)
    #     label(Y_sv)
    #     pot_type(PAW)
    # type(GGA,GGAU,HF)
    # is_hubbard

    @classmethod
    def _from_toolkit(
        cls,
        structure: ToolkitStructure | str = None,
        energy: float = None,
        as_dict: bool = False,
    ):
        if isinstance(structure, str):
            structure = ToolkitStructure.from_database_string(structure)

        # Given energy, this function builds the rest of the required fields
        # for this class as an object (or as a dictionary).
        data = dict(energy=energy) if energy else {}

        # if a structure is present, we can update that information as well.
        if structure and energy:
            epa_data = {"energy_per_atom": energy / structure.num_sites}
            data.update(epa_data)

        # OPTIMIZE: I try calculating these when each structure is added, but
        # this would be too slow. Instead, I have the user call the
        # update_all_stabilites method on a cycle.
        # energy_above_hull=None,
        # is_stable=None,
        # decomposes_to=None,

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return data if as_dict else cls(**data)

    @classmethod
    def update_chemical_system_stabilities(
        cls,
        chemical_system: str,
        workflow_name: str = None,
    ):

        phase_diagram, entries, entries_pmg = cls.get_phase_diagram(
            chemical_system,
            return_entries=True,
            workflow_name=workflow_name,
        )

        # now go through the entries and update stability values
        for entry, entry_pmg in zip(entries, entries_pmg):

            decomp, hull_energy = phase_diagram.get_decomp_and_e_above_hull(entry_pmg)

            entry.energy_above_hull = hull_energy

            entry.is_stable = True if hull_energy == 0 else False

            # OPTIMIZE: I would like this to point to another entry specifically
            # but this will take more work.
            entry.decomposes_to = (
                [d.composition.formula for d in decomp] if hull_energy != 0 else []
            )

            entry.formation_energy = phase_diagram.get_form_energy(entry_pmg)
            entry.formation_energy_per_atom = phase_diagram.get_form_energy_per_atom(
                entry_pmg
            )

        # Now that we updated our objects, we want to collectively update them
        cls.objects.bulk_update(
            objs=entries,
            fields=[
                "energy_above_hull",
                "is_stable",
                "decomposes_to",
                "formation_energy",
                "formation_energy_per_atom",
            ],
            # updating extremely large systems (>3k structures) can cause this
            # to time-out and crash. We therefore update in batches of 500
            batch_size=500,
        )

    @classmethod
    def update_all_stabilities(cls, workflow_name: str = None):

        # grab all unique chemical systems
        chemical_systems = cls.objects.values_list(
            "chemical_system", flat=True
        ).distinct()

        # Now  go through each and run the analysis.
        # OPTIMIZE: Some systems will be analyzed multiple times. For example,
        # C would be repeatedly updated through C, C-O, Y-C-F, etc.
        for chemical_system in track(chemical_systems):
            try:
                cls.update_chemical_system_stabilities(
                    chemical_system,
                    workflow_name,
                )
            except ValueError as exception:
                logging.warning(f"Failed for {chemical_system} with error: {exception}")

    @classmethod
    def get_phase_diagram(
        cls,
        chemical_system: str,
        workflow_name: str = None,
        return_entries: bool = False,
    ) -> PhaseDiagram:

        if workflow_name is None and hasattr(cls, "workflow_name"):
            raise Exception(
                "This table contains results from multiple workflows, so you must "
                "provide a workflow_name as an input to indicate which entries "
                "should be loaded/updated."
            )

        # if we have a multi-element system, we need to include subsystems as
        # well. ex: Na --> Na, Cl, Na-Cl
        subsystems = get_chemical_subsystems(chemical_system)

        # grab all entries for this chemical system
        entries = cls.objects.filter(
            # workflow_name="relaxation.vasp.staged",
            chemical_system__in=subsystems,
            energy__isnull=False,  # only completed calculations
        )
        # add an extra filter if provided
        if workflow_name:
            entries = entries.filter(workflow_name=workflow_name)

        # now make the queryy
        entries = entries.only("id", "energy", "formula_full").all()

        # convert to pymatgen PDEntries and build into PhaseDiagram object
        entries_pmg = []
        for entry in entries:
            pde = PDEntry(
                composition=entry.formula_full,
                energy=entry.energy,
                # name=entry.id,  see bug below
            )

            # BUG: pymatgen grabs entry_id, when it should really be grabbing name.
            # https://github.com/materialsproject/pymatgen/blob/de17dd84ba90dbf7a8ed709a33d894a4edb82d02/pymatgen/analysis/phase_diagram.py#L2926
            pde.entry_id = f"id={entry.id}"
            entries_pmg.append(pde)

        phase_diagram = PhaseDiagram(entries_pmg)

        return (
            phase_diagram
            if not return_entries
            else (
                phase_diagram,
                entries,
                entries_pmg,
            )
        )


class HullDiagram(PlotlyFigure):

    method_type = "classmethod"

    def get_plot(
        table,  # Thermodynamics + Structure table
        chemical_system: str,
        workflow_name: str = None,
        show_unstable_up_to: float = float("inf"),
    ):

        phase_diagram = table.get_phase_diagram(chemical_system, workflow_name)

        # alternatively use backend="matplotlib"
        plotter = PDPlotter(phase_diagram, show_unstable=show_unstable_up_to)
        # Only shows structures up to X eV above hull

        plot = plotter.get_plot(label_unstable=False)

        return plot


# register all plotting methods to the database table
for _plot in [HullDiagram]:
    _plot.register_to_class(Thermodynamics)
