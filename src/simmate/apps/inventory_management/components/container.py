from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import cached_property

from django.db import transaction
from django.utils import timezone

from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import (
    MoleculeInput,
    StructureInput,
)

from ..datastores import SubstanceDatastore
from ..models import (
    Batch,
    Container,
    Mixture,
    StorageLocation,
    Substance,
    UsageLog,
)


class ContainerComponent(TableComponent, MoleculeInput, StructureInput):
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

    # A new container is either added to an existing batch or to a new batch.
    # For new batches, this form also gets (or registers) the substance or
    # mixture that the batch is of, and logs the reagents used to make it.
    # Batch and mixture inputs are prefixed with "batch__" and "mixture__"
    # so that they are not mistaken for container columns.

    required_inputs = [
        "location_id",
        # "barcode",
        "initial_amount",
        "amount_units",
    ]

    batch_mode_options = [
        ("new", "New batch"),
        ("existing", "Existing batch"),
    ]

    contents_type_options = [
        ("substance", "Substance"),
        ("mixture", "Mixture"),
    ]

    mixture__mixture_type_options = Mixture.mixture_type_options

    batch__batch_type_options = Batch.batch_type_options

    post_data_mappings = {
        # each reagent row gives one entry to these lists. They stay as str
        # so that blank rows can be parsed
        "reagent_containers": list[str],
        "reagent_amounts": list[str],
        # can otherwise be parsed to an int (e.g. a single line "123")
        "mixture__components": str,
        "mixture_id": str,
    }

    def mount_for_create(self):
        self.update_form("amount_units", "mg")
        self.update_form("is_depleted", False)
        self.update_form("batch_mode", "new")
        self.update_form("contents_type", "substance")
        self.update_form("reagent_containers", [])
        self.update_form("reagent_amounts", [])

    def on_change_hook__structure__file(self):
        self.load_structure("structure")

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

    @property
    def mixture_components(self) -> list[str]:
        """
        The substance IDs or SMILES of a new mixture, given one per line.
        """
        lines = (self.form_data.get("mixture__components") or "").splitlines()
        return [line.strip() for line in lines if line.strip()]

    def add_reagent(self):
        self.form_data["reagent_containers"].append("")
        self.form_data["reagent_amounts"].append("")

    def remove_reagent(self, index: int):
        self.form_data["reagent_containers"].pop(index)
        self.form_data["reagent_amounts"].pop(index)

    def check_form_for_create(self):
        self.check_required_inputs()

        if self.form_data.get("batch_mode") == "existing":
            batch_id = self.form_data.get("batch_id")
            if not batch_id or not Batch.objects.filter(id=batch_id).exists():
                self.form_errors.append(
                    "'batch_id' must be the ID of an existing batch."
                )
            return  # the remaining inputs are only for new batches

        # The substance or mixture of the new batch, which is given either by
        # its ID or by what is in it. Giving both is an error rather than
        # picking one, as the user likely made a mistake.
        if self.form_data.get("contents_type") == "substance":
            substance_id = self.form_data.get("substance_id")
            molecule = self.form_data.get("molecule")
            structure = self.form_data.get("structure")
            # these are False if they failed to load
            has_molecule = molecule is not None and molecule is not False
            has_structure = structure is not None and structure is not False
            if molecule is False or structure is False:
                self.form_errors.append(
                    "The molecule or crystal structure failed to load."
                )
            elif substance_id and (has_molecule or has_structure):
                self.form_errors.append(
                    "Give either a substance ID or a molecule/crystal structure (not both)."
                )
            elif substance_id:
                try:
                    Substance.get_by_id(substance_id)
                except Substance.DoesNotExist as error:
                    self.form_errors.append(str(error))
            elif not (has_molecule or has_structure):
                self.form_errors.append(
                    "Give a substance ID, or load a molecule and/or crystal structure."
                )
        else:
            mixture_id = self.form_data.get("mixture_id")
            mixture_type = self.form_data.get("mixture__mixture_type")
            components = self.mixture_components
            if mixture_id and (mixture_type or components):
                self.form_errors.append(
                    "Give either an existing mixture ID or a new mixture (not both)."
                )
            elif mixture_id:
                try:
                    Mixture.get_by_display_id(mixture_id)
                except Mixture.DoesNotExist as error:
                    self.form_errors.append(str(error))
            elif not (mixture_type and components):
                self.form_errors.append(
                    "Give an existing mixture ID, or a mixture type and at least "
                    "one component for a new mixture."
                )
            else:
                for line in components:
                    if Substance.validate_id(line):
                        try:
                            Substance.get_by_id(line)
                        except Substance.DoesNotExist as error:
                            self.form_errors.append(str(error))
                    else:
                        try:
                            ToolkitMolecule.from_smiles(line)
                        except Exception:
                            self.form_errors.append(
                                f"Mixture component '{line}' is not a substance ID or valid SMILES."
                            )

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

    def unmount_for_create(self):
        self.update_form("current_amount", self.form_data["initial_amount"])
        super().unmount_for_create()

    def save_to_db_for_create(self):
        user_id = self.request.user.id

        with transaction.atomic():
            if self.form_data["batch_mode"] == "new":
                is_mixture = self.form_data["contents_type"] == "mixture"
                substance_id = None
                mixture = None

                if not is_mixture and self.form_data.get("substance_id"):
                    substance_id = Substance.get_by_id(
                        self.form_data["substance_id"]
                    ).id
                elif not is_mixture:
                    # This is the single entry point for registering substances,
                    # and it gives the existing ID if one is already registered
                    substance_id = SubstanceDatastore.get_or_create_id(
                        molecule=self.form_data.get("molecule"),
                        structure=self.form_data.get("structure"),
                        registered_by_id=user_id,
                    )
                elif self.form_data.get("mixture_id"):
                    mixture = Mixture.get_by_display_id(self.form_data["mixture_id"])
                else:
                    mixture = Mixture.objects.create(
                        id_prefix=Mixture.generate_id_prefix(),
                        mixture_type=self.form_data["mixture__mixture_type"],
                        common_name=self.form_data.get("mixture__common_name"),
                        description=self.form_data.get("mixture__description"),
                    )
                    # components are substance IDs or SMILES (which are
                    # registered all at once if needed)
                    component_ids = []
                    new_components = []
                    for line in self.mixture_components:
                        if Substance.validate_id(line):
                            component_ids.append(Substance.get_by_id(line).id)
                        else:
                            new_components.append(
                                dict(molecule=line, registered_by_id=user_id)
                            )
                    if new_components:
                        component_ids += SubstanceDatastore.get_or_create_ids(
                            new_components
                        )
                    mixture.substances.set(component_ids)

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
                    is_mixture=is_mixture,
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
