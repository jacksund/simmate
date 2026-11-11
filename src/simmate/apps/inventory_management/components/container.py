from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import cached_property

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.website.data_explorer.components import (
    QuickSearchComponent,
    TableComponent,
)
from simmate.website.htmx.components import (
    MoleculeInput,
    StructureInput,
)
from simmate.website.htmx.components.mixins import PeriodicTableInput

from ..datastores import SubstanceDatastore
from ..models import (
    Batch,
    Container,
    Mixture,
    MixtureComponent,
    StorageLocation,
    Substance,
    UsageLog,
)


class ContainerComponent(
    TableComponent,
    MoleculeInput,
    StructureInput,
    PeriodicTableInput,
):
    table = Container

    template_names = {
        "entries": "inventory_management/container/table.html",
        "entry": "inventory_management/container/view.html",
        "search": "inventory_management/container/form.html",
        "create": "inventory_management/container/form.html",
        "update": "inventory_management/container/form.html",
    }

    display_name = "Containers"
    description_short = (
        "Containers are specific vessels that contain part (or all) of a batch. A "
        "single batch can have multiple containers because batches might need to be "
        "split up and/or have different storage destinations."
    )

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "create",
        "update",
    ]

    # -------------------------------------------------------------------------

    # CREATE

    # Registering a container has two sections:
    #   1. Contents & Batch: the user searches for what is in the container and
    #      selects an existing substance or mixture, or describes a new one.
    #      Existing contents can be added to one of their batches. Otherwise,
    #      a new batch is made, along with a log of the reagents used to make it.
    #   2. Container Info: where the container is stored and how much is in it.
    # What was selected is stored as the `contents_mode`, which is one of
    # "existing_substance", "new_substance", "existing_mixture", "new_mixture",
    # or None (nothing selected yet). Batch and mixture inputs are prefixed with
    # "batch__" and "mixture__" so that they are not mistaken for container
    # columns.

    required_inputs = [
        "location_id",
        # "barcode",
        "initial_amount",
        "amount_units",
    ]

    mixture__mixture_type_options = Mixture.mixture_type_options

    batch__batch_type_options = Batch.batch_type_options

    post_data_mappings = {
        # can otherwise be parsed to an int (e.g. a typed ID like "123")
        "search_query": str,
        # each reagent or mixture component row gives one entry to these
        # lists. They stay as str so that blank rows can be parsed
        "reagent_containers": list[str],
        "reagent_amounts": list[str],
        "component_substances": list[str],
        "component_roles": list[str],
        "component_amounts": list[str],
        "component_units": list[str],
    }

    search_results: dict = None
    """
    The substances and mixtures that match the `search_query` (see `run_search`).
    """

    is_from_description: bool = False
    """
    Whether the form was just filled in from the `search_query` by
    `run_search` (from a description), so the user is asked to review it.
    """

    active_panel: str = None
    """
    The search helper that is open below the search bar ("examples",
    "periodic_table", or "sketcher"), if any. These are the same helpers as the
    quick search (see `QuickSearchComponent`).
    """

    search_examples = [
        # (section, icon, [(label, query), ...])
        (
            "IDs & Names",
            "upc",
            [
                ("BCD-012-3456", "BCD-012-3456"),
                ("BCDF-123 (mixture)", "BCDF-123"),
                ("DMSO", "DMSO"),
            ],
        ),
        ("Formulas & Systems", "funnel", [("NaCl", "NaCl"), ("Li-Co-O", "Li-Co-O")]),
        ("SMILES Strings", "hexagon", [("CCO (Ethanol)", "CCO")]),
        (
            "Descriptions",
            "chat-text",
            [
                (
                    "0.1M solution of NaCl in water",
                    "0.1M solution of NaCl in water",
                )
            ],
        ),
    ]
    """
    The example searches shown in the "examples" panel.
    """

    def mount_for_create(self):
        self.update_form("amount_units", "mg")
        self.update_form("is_depleted", False)
        self.update_form("search_query", "")
        self.update_form("reagent_containers", [])
        self.update_form("reagent_amounts", [])
        self.clear_contents()

    def on_change_hook__structure__file(self):
        self.load_structure("structure")

    # -------------------------------------------------------------------------

    # Contents (searching for and selecting a substance or mixture)

    def toggle_panel(self):
        """
        Opens or closes one of the search helpers (see `active_panel`).
        """
        panel = self.post_data.get("panel")
        self.active_panel = None if self.active_panel == panel else panel

    def set_example(self):
        """
        Searches for one of the examples in the "examples" panel.
        """
        self.form_data["search_query"] = self.post_data.get("query", "")
        self.active_panel = None
        self.run_search()

    def on_change_hook__sketch__molecule_sketcher(self):
        # The sketcher fills the search bar with the drawn molecule's SMILES.
        # The sketch is kept in the form (rather than loaded and popped like
        # other molecule inputs) so that it only replaces the search when the
        # drawing changes.
        sketch = self.form_data.get("sketch__molecule_sketcher")
        try:
            smiles = ToolkitMolecule.from_dynamic(sketch).to_smiles()
        except Exception:
            return  # e.g. an empty or unfinished drawing
        if smiles:
            self.form_data["search_query"] = smiles

    def run_search(self, parse_descriptions: bool = True):
        """
        Finds the substances and mixtures that match the `search_query`, which
        can be a substance or mixture ID, a name, a formula, or a SMILES.

        Queries that match nothing (and aren't an ID, formula, or SMILES) are
        treated as a plain-text description, such as "0.1M solution of NaCl in
        water". The description is parsed to fill in the form, where a single
        substance is then searched for like any other query and a mixture is
        filled in as a new mixture.

        Args:
            parse_descriptions: Whether to parse queries that match nothing as
                a description. This is turned off when searching for the
                substance of a parsed description, so it is only parsed once.
        """
        query = str(self.form_data.get("search_query") or "").strip()
        self.is_from_description = False
        if not query:
            self.search_results = None
            return

        # Substances are searched the same way as the quick search
        search_field, value = QuickSearchComponent.parse_query(
            query,
            substance_table=Substance,
        )
        if search_field == "id":
            try:
                # follows merged IDs and loads datastore-only substances
                substances = [Substance.get_by_id(value)]
            except Substance.DoesNotExist:
                substances = []
        else:
            url_filter = QuickSearchComponent.substance_filters[search_field]
            substances = list(
                Substance.objects.filter(**{url_filter: value})
                .select_related("molecule", "structure")
                .order_by("id")[:5]
            )

        # Mixtures match by their ID or name, or by containing one of the
        # substances found (e.g. "NaCl" finds a 0.1 M NaCl solution)
        mixtures = []
        try:
            mixtures.append(Mixture.get_by_display_id(query))
        except Mixture.DoesNotExist:
            pass
        mixtures += (
            Mixture.objects.filter(
                Q(common_name__icontains=query) | Q(substances__in=substances)
            )
            .exclude(id__in=[mixture.id for mixture in mixtures])
            .prefetch_related("substances")
            .distinct()
            .order_by("-id")[:5]
        )

        self.search_results = dict(
            query=query,
            substances=substances,
            mixtures=mixtures,
            # SMILES that aren't registered yet can be registered as new
            is_new_smiles=search_field == "inchi_key" and not substances,
        )
        if not parse_descriptions or search_field != "name" or substances or mixtures:
            return

        # Nothing matched, so the query is parsed as a description (by an llm)
        from simmate.apps.chatbot.parsers import parse_container_description

        parsed = parse_container_description(query)

        self.clear_contents()

        if parsed.get("contents_type") == "substance" and parsed.get("substance"):
            # a single substance is looked up like any other search
            self.form_data["search_query"] = parsed["substance"]
            self.run_search(parse_descriptions=False)

        elif parsed.get("contents_type") == "mixture":
            self.form_data["contents_mode"] = "new_mixture"
            self.form_data["batch_mode"] = "new"
            mixture = parsed.get("mixture") or {}
            for key in ["mixture_type", "common_name", "description"]:
                if mixture.get(key):
                    self.form_data[f"mixture__{key}"] = mixture[key]
            for component in mixture.get("components") or []:
                for key, form_key in [
                    ("substance", "component_substances"),
                    ("role", "component_roles"),
                    ("amount", "component_amounts"),
                    ("amount_units", "component_units"),
                ]:
                    value = component.get(key)
                    self.form_data[form_key].append(
                        str(value) if value is not None else ""
                    )

            # Existing mixtures that have all of these components are offered
            # in case this mixture is already registered
            rows = [row for row in self.component_rows if row["status"] != "blank"]
            mixtures = []
            if rows and all(row["status"] == "existing" for row in rows):
                matches = Mixture.objects.all()
                for row in rows:
                    matches = matches.filter(substances__id=row["substance_id"])
                mixtures = list(
                    matches.prefetch_related("substances")
                    .distinct()
                    .order_by("-id")[:5]
                )
            self.search_results["mixtures"] = mixtures

        else:
            return  # nothing could be parsed, so "nothing found" is shown

        for key, value in (parsed.get("batch") or {}).items():
            if value not in (None, ""):
                self.form_data[f"batch__{key}"] = value
        for key, value in (parsed.get("container") or {}).items():
            if value not in (None, ""):
                self.form_data[key] = value

        self.is_from_description = True

    def select_substance(self, substance_id: str):
        substance = Substance.get_by_id(substance_id)
        self.clear_contents()
        self.form_data["contents_mode"] = "existing_substance"
        self.form_data["substance_id"] = substance.id
        # the user picks from the batches table, unless there are none
        self.form_data["batch_mode"] = None if self.existing_batches else "new"

    def select_mixture(self, mixture_id: str):
        mixture = Mixture.get_by_display_id(str(mixture_id))
        self.clear_contents()
        self.form_data["contents_mode"] = "existing_mixture"
        self.form_data["mixture_id"] = mixture.display_id
        # the user picks from the batches table, unless there are none
        self.form_data["batch_mode"] = None if self.existing_batches else "new"

    def select_new_substance(self):
        """
        Uses the SMILES that was searched for as a new substance.
        """
        molecule = ToolkitMolecule.from_smiles(self.search_results["query"])
        self.clear_contents()
        self.form_data["contents_mode"] = "new_substance"
        self.form_data["batch_mode"] = "new"
        self.form_data["molecule"] = molecule
        # draws the molecule in the molecule input
        self.js_actions.append(
            {
                "add_mol_viewer": [
                    f"molecule-{self.component_id}-image",
                    molecule.to_sdf(),
                    300,
                    300,
                ]
            }
        )

    def clear_contents(self):
        """
        Unsets the substance or mixture (and batch) selected for this
        container, so that the user can search again. The search results are
        kept so that the user can go back to them.
        """
        for key in [
            "substance_id",
            "mixture_id",
            "molecule",
            "molecule_original",
            "structure",
            "mixture__mixture_type",
            "mixture__common_name",
            "mixture__description",
            "batch_id",
        ]:
            self.form_data.pop(key, None)
        self.form_data.update(
            contents_mode=None,
            batch_mode=None,
            component_substances=[],
            component_roles=[],
            component_amounts=[],
            component_units=[],
        )
        self.is_from_description = False

    @property
    def selected_entry(self) -> Substance | Mixture | None:
        """
        The existing substance or mixture that was selected, if any.
        """
        contents_mode = self.form_data.get("contents_mode")
        if contents_mode == "existing_substance":
            return Substance.get_by_id(self.form_data["substance_id"])
        elif contents_mode == "existing_mixture":
            return Mixture.get_by_display_id(self.form_data["mixture_id"])
        return None

    # -------------------------------------------------------------------------

    # New mixture components

    component_role_options = MixtureComponent.role_options

    component_units_options = MixtureComponent.amount_units_options

    @property
    def component_rows(self) -> list[dict]:
        """
        The rows of the new mixture's components table. Each row's `status`
        is whether its substance is already registered ("existing", with its
        `substance_id`), will be registered when saved ("new"), is not a valid
        substance ID or SMILES ("invalid"), or was left empty ("blank").
        """
        rows = []
        for substance, role, amount, units in zip(
            self.form_data["component_substances"],
            self.form_data["component_roles"],
            self.form_data["component_amounts"],
            self.form_data["component_units"],
        ):
            row = dict(
                substance=substance.strip(),
                role=role,
                amount=amount.strip(),
                units=units,
                substance_id=None,
                inchi_key=None,
            )
            if not row["substance"]:
                row["status"] = "blank"
            elif Substance.validate_id(row["substance"]):
                try:
                    row["substance_id"] = Substance.get_by_id(row["substance"]).id
                    row["status"] = "existing"
                except Substance.DoesNotExist:
                    row["status"] = "invalid"
            else:
                try:
                    molecule = ToolkitMolecule.from_smiles(row["substance"])
                    row["inchi_key"] = molecule.to_inchi_key()
                except Exception:
                    row["status"] = "invalid"
                else:
                    # this is only a preview, as the final match is made by
                    # `SubstanceDatastore.get_or_create_ids` when saved
                    row["substance_id"] = (
                        Substance.objects.filter(molecule__inchi_key=row["inchi_key"])
                        .values_list("id", flat=True)
                        .first()
                    )
                    row["status"] = "existing" if row["substance_id"] else "new"
            rows.append(row)
        return rows

    def add_component(self):
        self.form_data["component_substances"].append("")
        self.form_data["component_roles"].append("")
        self.form_data["component_amounts"].append("")
        self.form_data["component_units"].append("")

    def remove_component(self, index: int):
        self.form_data["component_substances"].pop(index)
        self.form_data["component_roles"].pop(index)
        self.form_data["component_amounts"].pop(index)
        self.form_data["component_units"].pop(index)

    # -------------------------------------------------------------------------

    # Batch (existing or new) and the reagents used to make new batches

    @property
    def existing_batches(self) -> list[Batch]:
        """
        The most recent batches of the selected substance or mixture.
        """
        entry = self.selected_entry
        if entry is None:
            return []
        column = "substance" if isinstance(entry, Substance) else "mixture"
        return list(Batch.objects.filter(**{column: entry}).order_by("-id")[:10])

    def select_batch(self, batch_id: int = None):
        """
        Adds the container to an existing batch, or to a new batch when no
        `batch_id` is given.
        """
        if batch_id is None:
            self.form_data["batch_mode"] = "new"
            self.form_data.pop("batch_id", None)
            return
        batch = Batch.objects.get(id=batch_id)
        self.form_data["batch_mode"] = "existing"
        self.form_data["batch_id"] = batch.id
        # containers of a batch share its units (see `check_form_for_create`)
        if batch.amount_units:
            self.form_data["amount_units"] = batch.amount_units

    def clear_batch(self):
        """
        Goes back to picking from the batches of the selected chemical.
        """
        self.form_data["batch_mode"] = None
        self.form_data.pop("batch_id", None)

    @property
    def reagent_rows(self) -> list[tuple]:
        """
        The (container, amount) of each reagent row in the form.
        """
        return list(
            zip(
                self.form_data["reagent_containers"],
                self.form_data["reagent_amounts"],
            )
        )

    def add_reagent(self):
        self.form_data["reagent_containers"].append("")
        self.form_data["reagent_amounts"].append("")

    def remove_reagent(self, index: int):
        self.form_data["reagent_containers"].pop(index)
        self.form_data["reagent_amounts"].pop(index)

    # -------------------------------------------------------------------------

    @property
    def section_states(self) -> dict[str, str]:
        """
        The state of each form section ("chemical", "batch", and "container"),
        which sets its color in the form. Sections that are filled in are
        "done", the first section that is not is "active", and any after it
        are "waiting". The container section's inputs are hidden while it is
        "waiting". These are only a guide for the user, and the full checks
        are in `check_form_for_create`. Only the create form has states.
        """
        if self.component_type != "create":
            return {}

        contents_mode = self.form_data.get("contents_mode")
        if contents_mode == "new_substance":
            is_chemical_done = isinstance(
                self.form_data.get("molecule"), ToolkitMolecule
            )
        elif contents_mode == "new_mixture":
            rows = [row for row in self.component_rows if row["status"] != "blank"]
            is_chemical_done = bool(
                self.form_data.get("mixture__mixture_type")
                and rows
                and all(row["status"] != "invalid" for row in rows)
            )
        else:
            is_chemical_done = contents_mode is not None

        # all new batch inputs are optional, so the batch type is used as the
        # sign that the user filled them in
        batch_mode = self.form_data.get("batch_mode")
        if batch_mode == "existing":
            is_batch_done = bool(self.form_data.get("batch_id"))
        elif batch_mode == "new":
            is_batch_done = bool(self.form_data.get("batch__batch_type"))
        else:
            is_batch_done = False

        # the container section is only shown once the sections before it are
        # done, so it can't be done (or active) before them
        is_container_done = (
            is_chemical_done
            and is_batch_done
            and all(
                self.form_data.get(key) not in (None, "")
                for key in self.required_inputs
            )
        )

        states = {}
        is_active_found = False
        for section, is_done in [
            ("chemical", is_chemical_done),
            ("batch", is_batch_done),
            ("container", is_container_done),
        ]:
            if is_done:
                states[section] = "done"
            elif not is_active_found:
                states[section] = "active"
                is_active_found = True
            else:
                states[section] = "waiting"
        return states

    def check_form_for_create(self):
        self.check_required_inputs()

        # Contents
        contents_mode = self.form_data.get("contents_mode")
        if not contents_mode:
            self.form_errors.append(
                "Search for and select what is in this container, or start a "
                "new substance or mixture."
            )
        elif contents_mode == "new_substance":
            molecule = self.form_data.get("molecule")
            structure = self.form_data.get("structure")
            # these are False if they failed to load
            if molecule is False or structure is False:
                self.form_errors.append(
                    "The molecule or crystal structure failed to load."
                )
            elif molecule is None and structure is None:
                self.form_errors.append(
                    "Load a molecule and/or crystal structure for the new substance."
                )
        elif contents_mode == "new_mixture":
            if not self.form_data.get("mixture__mixture_type"):
                self.form_errors.append("Give the type of the new mixture.")
            rows = [row for row in self.component_rows if row["status"] != "blank"]
            if not rows:
                self.form_errors.append("Add at least one component to the mixture.")
            # Each substance can only be listed once (see MixtureComponent).
            # New SMILES are compared by their InChIKey
            seen = set()
            for row in rows:
                name = row["substance"]
                if row["status"] == "invalid":
                    self.form_errors.append(
                        f"Mixture component '{name}' is not a substance ID or valid SMILES."
                    )
                    continue
                key = row["substance_id"] or row["inchi_key"]
                if key in seen:
                    self.form_errors.append(
                        f"Mixture component '{name}' is listed more than once."
                    )
                seen.add(key)
                if row["amount"]:
                    try:
                        float(row["amount"])
                    except ValueError:
                        self.form_errors.append(
                            f"The amount of '{name}' must be a number (got '{row['amount']}')."
                        )
                    if not row["units"]:
                        self.form_errors.append(
                            f"Give the units for the amount of '{name}'."
                        )

        # Batch
        if self.form_data.get("batch_mode") == "existing":
            batch = Batch.objects.filter(id=self.form_data.get("batch_id")).first()
            if not batch:
                self.form_errors.append(
                    "Select an existing batch, or choose to make a new batch."
                )
            # Batch totals are sums of the container amounts, so every
            # container of a batch must use the same units
            elif batch.amount_units and batch.amount_units != self.form_data.get(
                "amount_units"
            ):
                self.form_errors.append(
                    f"The selected batch is measured in '{batch.amount_units}', "
                    "so the container's amount must use the same units."
                )
        elif self.form_data.get("batch_mode") == "new":
            for container, amount in self.reagent_rows:
                if not container and not amount:
                    continue  # blank rows are skipped
                try:
                    Container.get_by_barcode_or_id(container)
                except Container.DoesNotExist as error:
                    self.form_errors.append(str(error))
                try:
                    if Decimal(amount) <= 0:
                        raise InvalidOperation()
                except (InvalidOperation, TypeError):
                    self.form_errors.append(
                        f"Reagent amounts must be greater than 0 (got '{amount}')."
                    )
        elif self.form_data.get("contents_mode"):
            self.form_errors.append(
                "Select an existing batch, or choose to make a new batch."
            )

        # Container
        initial_amount = self.form_data.get("initial_amount")
        if initial_amount not in (None, ""):
            try:
                is_positive = Decimal(str(initial_amount)) > 0
            except InvalidOperation:
                is_positive = False
            if not is_positive:
                self.form_errors.append(
                    "The container's amount must be greater than 0."
                )
        # Scanned barcodes must point to a single container
        barcode = self.form_data.get("barcode")
        if barcode and Container.objects.filter(barcode=str(barcode)).exists():
            self.form_errors.append(
                f"Another container already has the barcode '{barcode}'."
            )

    def unmount_for_create(self):
        self.update_form("current_amount", self.form_data["initial_amount"])
        super().unmount_for_create()

    def save_to_db_for_create(self):
        user_id = self.request.user.id
        contents_mode = self.form_data["contents_mode"]

        with transaction.atomic():
            if self.form_data["batch_mode"] == "new":
                substance_id = None
                mixture = None

                if contents_mode == "existing_substance":
                    substance_id = Substance.get_by_id(
                        self.form_data["substance_id"]
                    ).id
                elif contents_mode == "new_substance":
                    # This is the single entry point for registering substances,
                    # and it gives the existing ID if one is already registered
                    substance_id = SubstanceDatastore.get_or_create_id(
                        molecule=self.form_data.get("molecule"),
                        structure=self.form_data.get("structure"),
                        registered_by_id=user_id,
                    )
                elif contents_mode == "existing_mixture":
                    mixture = Mixture.get_by_display_id(self.form_data["mixture_id"])
                else:
                    mixture = Mixture.objects.create(
                        id_prefix=Mixture.generate_id_prefix(),
                        mixture_type=self.form_data["mixture__mixture_type"],
                        common_name=self.form_data.get("mixture__common_name"),
                        description=self.form_data.get("mixture__description"),
                    )
                    # Components given by ID are already registered, and the
                    # SMILES are registered all at once (if needed)
                    rows = [
                        row for row in self.component_rows if row["status"] != "blank"
                    ]
                    smiles_rows = [
                        row
                        for row in rows
                        if not Substance.validate_id(row["substance"])
                    ]
                    if smiles_rows:
                        new_ids = SubstanceDatastore.get_or_create_ids(
                            [
                                dict(
                                    molecule=row["substance"], registered_by_id=user_id
                                )
                                for row in smiles_rows
                            ]
                        )
                        for row, new_id in zip(smiles_rows, new_ids):
                            row["substance_id"] = new_id
                    MixtureComponent.objects.bulk_create(
                        [
                            MixtureComponent(
                                mixture=mixture,
                                substance_id=row["substance_id"],
                                role=row["role"] or None,
                                amount=float(row["amount"]) if row["amount"] else None,
                                amount_units=row["units"] or None,
                            )
                            for row in rows
                        ]
                    )

                batch_columns = {
                    key.removeprefix("batch__"): value
                    for key, value in self.form_data.items()
                    if key.startswith("batch__")
                }
                if batch_columns.get("expiration_date"):
                    batch_columns["expiration_date"] = timezone.make_aware(
                        datetime.fromisoformat(batch_columns["expiration_date"])
                    )
                batch = Batch.objects.create(
                    is_mixture=mixture is not None,
                    substance_id=substance_id,
                    mixture=mixture,
                    supplied_by_id=user_id,
                    amount_units=self.form_data["amount_units"],
                    **batch_columns,
                )
                # Batch numbers count the batches of each substance (or
                # mixture). They are set from the IDs once the batch exists,
                # so two batches made at once don't take the same number
                batch.batch_number = Batch.objects.filter(
                    substance_id=substance_id,
                    mixture=mixture,
                    id__lte=batch.id,
                ).count()
                batch.save(update_fields=["batch_number"])
                self.table_entry.batch = batch

                # The reagents used to make the new batch. Each one is logged
                # as material taken from its container, and its batch is
                # linked as a parent of the new batch
                parent_batch_ids = set()
                for container, amount in self.reagent_rows:
                    if not container and not amount:
                        continue  # blank rows are skipped
                    source_container = Container.get_by_barcode_or_id(container)
                    usage_log = UsageLog.objects.create(
                        source_container=source_container,
                        user_id=user_id,
                        amount_removed=Decimal(amount),
                        destination_batch=batch,
                    )
                    usage_log.deduct_from_container()
                    if source_container.batch_id:
                        parent_batch_ids.add(source_container.batch_id)
                batch.parent_batches.add(*parent_batch_ids)

            super().save_to_db_for_create()  # saves the container
            Batch.update_cached_columns([self.table_entry.batch_id])

    # -------------------------------------------------------------------------

    # UPDATE

    def check_form_for_update(self):
        # the create checks are only for registering new containers
        self.check_required_inputs()

    def save_to_db_for_update(self):
        # The default repeats `save_to_db_for_create`, which also registers
        # new batches here. Updates only save the container.
        super().save_to_db_for_create()

    # -------------------------------------------------------------------------

    @cached_property
    def location_options(self):
        # TODO: limit user/project-linked locations
        locations = (
            StorageLocation.objects.order_by("name").values_list("id", "name").all()
        )
        return [(id, name) for id, name in locations]
