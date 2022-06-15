# -*- coding: utf-8 -*-

from tqdm import tqdm

from simmate.toolkit import Structure as ToolkitStructure
from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.utilities import get_chemical_subsystems

from pymatgen.analysis.phase_diagram import PDEntry
from pymatgen.analysis.phase_diagram import PhaseDiagram


class Thermodynamics(DatabaseTable):
    class Meta:
        abstract = True

    base_info = ["energy"]

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
        structure: ToolkitStructure,
        energy: float = None,
        as_dict: bool = False,
    ):

        # TODO: should structure be optional?

        # Given energy, this function builds the rest of the required fields
        # for this class as an object (or as a dictionary).
        data = (
            dict(
                energy=energy,
                energy_per_atom=energy / structure.num_sites,
                energy_above_hull=None,
                is_stable=None,
                decomposes_to=None,
            )
            if energy
            else {}
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return data if as_dict else cls(**data)

    @classmethod
    def update_chemical_system_stabilities(cls, chemical_system: str):

        # NOTE: I assume we are using a Child(Structure, Thermodynamics)

        # if we have a multi-element system, we need to include subsystems as
        # well. ex: Na --> Na, Cl, Na-Cl
        subsystems = get_chemical_subsystems(chemical_system)

        # grab all entries for this chemical system
        entries = (
            cls.objects.filter(
                chemical_system__in=subsystems,
                energy__isnull=False,  # only completed calculations
            )
            .only("energy", "formula_full")
            .all()
        )

        # convert to pymatgen PDEntries and build into PhaseDiagram object
        entries_pmg = [PDEntry(entry.formula_full, entry.energy) for entry in entries]
        phase_diagram = PhaseDiagram(entries_pmg)

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
    def update_all_stabilities(cls):

        # grab all unique chemical systems
        chemical_systems = cls.objects.values_list(
            "chemical_system", flat=True
        ).distinct()

        # Now  go through each and run the analysis.
        # OPTIMIZE: Some systems will be analyzed multiple times. For example,
        # C would be repeatedly updated through C, C-O, Y-C-F, etc.
        for chemical_system in tqdm(chemical_systems):
            try:
                cls.update_chemical_system_stabilities(chemical_system)
            except ValueError as exception:
                print(f"Failed for {chemical_system} with error: {exception}")

        # BUG: can't use parallel=True as an input
        # Because different systems may need to update a single one at the same
        # time, errors will be thrown due to row locking. For example, Y-C and
        # Sc-C system might both try to update a C structure at the same time
        # and one will throw an error.
        #
        # from simmate.configuration.dask import batch_submit
        #
        # batch_submit(
        #     function=cls.update_chemical_system_stabilities,
        #     args_list=chemical_systems,
        #     batch_size=1000,
        # )
