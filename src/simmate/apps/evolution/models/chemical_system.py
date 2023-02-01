# -*- coding: utf-8 -*-

import logging
import traceback
import warnings
from pathlib import Path

from simmate.database.base_data_types import Calculation, table_column
from simmate.toolkit import Composition
from simmate.utilities import get_chemical_subsystems, get_directory

# BUG: This prints a tqdm error so we silence it here.
with warnings.catch_warnings(record=True):
    from pymatgen.analysis.phase_diagram import PhaseDiagram


class ChemicalSystemSearch(Calculation):
    class Meta:
        app_label = "workflows"

    chemical_system = table_column.CharField(max_length=10, null=True, blank=True)
    subworkflow_name = table_column.CharField(max_length=200, null=True, blank=True)
    subworkflow_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    max_atoms = table_column.IntegerField(null=True, blank=True)
    max_stoich_factor = table_column.IntegerField(null=True, blank=True)
    singleshot_sources = table_column.JSONField(default=list, null=True, blank=True)

    # DEV NOTE: many of the methods below are copy/pasted from the fixed
    # composition table and functionality should be merged in the future.

    # -------------------------------------------------------------------------
    # Core methods that help grab key information about the search
    # -------------------------------------------------------------------------

    def to_toolkit(self) -> PhaseDiagram:
        phase_diagram = self.individuals_datatable.get_phase_diagram(
            chemical_system=self.chemical_system,
            workflow_name=self.subworkflow.name_full,
        )
        return phase_diagram

    @property
    def chemical_system_cleaned(self):
        # simply ordered elements in alphabetical order as that is how they
        # are stored in the database
        endpoint_compositions = [
            Composition(sys) for sys in self.chemical_system.split("-")
        ]
        elements = []
        for comp in endpoint_compositions:
            for element in comp.elements:
                element = str(element)
                if element not in elements:
                    elements.append(element)
        elements.sort()
        chemical_system = "-".join(elements)
        return chemical_system

    @property
    def chemical_subsystems(self):
        return get_chemical_subsystems(self.chemical_system_cleaned)

    @property
    def subworkflow(self):
        from simmate.workflows.utilities import get_workflow

        if self.subworkflow_name == "relaxation.vasp.staged":
            return get_workflow(self.subworkflow_name)
        else:
            raise Exception(
                "Only `relaxation.vasp.staged` is supported in early testing"
            )

    @property
    def individuals_datatable(self):
        return self.subworkflow.database_table

    @property
    def individuals(self):
        return self.individuals_datatable.objects.filter(
            chemical_system__in=self.chemical_subsystems,
            workflow_name=self.subworkflow_name,
        )

    @property
    def individuals_completed(self):
        return self.individuals.filter(energy_per_atom__isnull=False)

    @property
    def individuals_incomplete(self):
        # If there is an energy_per_atom, we can treat the calculation as completed
        return self.individuals.filter(energy_per_atom__isnull=True)

    @property
    def stable_structures(self):
        structures = self.individuals_completed.filter(energy_above_hull=0).to_toolkit()
        return structures

    @property
    def best_structure_for_each_composition(self):
        # BUG: for sqlite, you can't use distinct.
        # structures = (
        #     self.individuals_completed.order_by("energy_above_hull")
        #     .distinct("formula_reduced")
        #     .to_toolkit()
        # )

        # Instead, I just use pymatgen. This is slower but still works
        phase_diagram = self.to_toolkit()

        structures = [
            self.individuals.get(id=int(e.entry_id.split("=")[-1]))
            for e in phase_diagram.qhull_entries
        ]
        return [s.to_toolkit() for s in structures]

    def update_stabilities(self):
        self.individuals_datatable.update_chemical_system_stabilities(
            chemical_system=self.chemical_system_cleaned,
            workflow_name=self.subworkflow.name_full,
        )

    # -------------------------------------------------------------------------
    # Writing CSVs summaries and CIFs of best structures
    # -------------------------------------------------------------------------

    def write_output_summary(self, directory):
        # If the output fails to write, we have a non-critical issue that
        # doesn't affect the search. We therefore don't want to raise an
        # error here -- but instead warn the user and then continue the search
        try:
            if not self.individuals_completed.exists():
                logging.info("No structures completed yet. Skipping output writing.")
                return

            logging.info(f"Writing search summary to {directory}")

            super().write_output_summary(directory=directory)

            # update all chemical stabilites before creating the output files
            self.update_stabilities()

            self.individuals_datatable.write_hull_diagram_plot(
                chemical_system=self.chemical_system_cleaned,
                workflow_name=self.subworkflow.name_full,
                directory=directory,
                show_unstable_up_to=5,
            )

            stable_dir = get_directory(directory / "stable_structures")
            self.write_stable_structures(stable_dir)

            all_comps_dir = get_directory(directory / "best_structure_per_composition")
            self.write_stable_structures(all_comps_dir, include_best_metastable=True)

        except Exception as error:
            if (
                isinstance(error, ValueError)
                and "no entries for the terminal elements" in error.args[0]
            ):
                logging.warning(
                    "The convex hull and structure stabilities cannot be calculated "
                    "without terminal elements. Either manually submit pure-element "
                    "structures to your subworkflow, or make sure you run your "
                    "search with singleshot sources active (the default) AND "
                    "your database populated with third-party data. Output files "
                    "will not be written until this is done."
                )

            else:
                logging.warning(
                    "Failed to write the output summary. This issue will be silenced "
                    "to avoid stopping the search. But please report the following "
                    "error to our github: https://github.com/jacksund/simmate/issues/"
                )

                # prints the most recent exception traceback
                traceback.print_exc()

    def write_stable_structures(
        self,
        directory: Path,
        include_best_metastable: bool = False,
    ):
        # if the directory is filled, we need to delete all the files
        # before writing the new ones.
        for file in directory.iterdir():
            try:
                file.unlink()
            except OSError:
                logging.warning("Unable to delete a CIF file: {file}")
                logging.warning(
                    "Updating the 'best structures' directory involves deleting "
                    "and re-writing all CIF files each cycle. If you have a file "
                    "open while this step occurs, then you'll see this warning."
                    "Close your file for this to go away."
                )

        structures = (
            self.stable_structures
            if not include_best_metastable
            else self.best_structure_for_each_composition
        )

        for rank, structure in enumerate(structures):
            rank_cleaned = str(rank).zfill(2)  # converts 1 to 01
            structure_filename = directory / (
                f"rank-{str(rank_cleaned)}__"
                + f"id-{structure.database_object.id}"
                + f"id-{structure.composition.reduced_formula}.cif"
            )
            structure.to(filename=str(structure_filename), fmt="cif")

    def write_individuals_completed_full(self, directory: Path):
        columns = self.individuals_datatable.get_column_names()
        columns.remove("structure")
        df = self.individuals_completed.defer("structure").to_dataframe(columns)
        csv_filename = directory / "individuals_completed__ALLDATA.csv"
        df.to_csv(csv_filename)

    def write_individuals_completed(self, directory: Path):
        columns = [
            "id",
            "energy_per_atom",
            "finished_at",
            "source",
            "spacegroup__number",
        ]
        df = (
            self.individuals_completed.order_by(self.fitness_field)
            .only(*columns)
            .to_dataframe(columns)
        )
        # label the index column
        df.index.name = "rank"

        # make the timestamps easier to read
        def format_date(date):
            return date.strftime("%Y-%m-%d %H:%M:%S")

        df["finished_at"] = df.finished_at.apply(format_date)

        def format_parents(source):
            return source.get("parent_ids", None) if source else None

        df["parent_ids"] = df.source.apply(format_parents)

        def format_source(source):
            return (
                None
                if not source
                else source.get("creator", None) or source.get("transformation", None)
            )

        df["source"] = df.source.apply(format_source)

        # shorten the column name for easier reading
        df.rename(columns={"spacegroup__number": "spacegroup"}, inplace=True)

        md_filename = directory / "individuals_completed.md"
        df.to_markdown(md_filename)
