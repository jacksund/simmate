from itertools import pairwise

from django.db.models import Count, F, Prefetch

from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.toolkit import Structure
from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import (
    MoleculeInput,
    StructureInput,
)

from ..models import Container, MixtureComponent, Substance, UsageLog


class SubstanceComponent(TableComponent, MoleculeInput, StructureInput):
    table = Substance

    display_name = "Chemical Substances"
    description_short = (
        "A substance is a specific element or compound with uniform composition+structure. "
        "As a general rule of thumb, if there is a CAS number (from ACS) or "
        "CID (from PubChem) assigned to it, then it is likely a chemical substance. "
        "In addition, this table includes both specified and unspecified "
        "stereochemical compounds, where flat structures and those with "
        "'and'/'or' notations are separate entries. Allotropes are also "
        "separate entries."
    )

    template_names = {
        "entries": "inventory_management/substance/table.html",
        "entry": "inventory_management/substance/view.html",
        "search": "inventory_management/substance/form.html",
        "create": "inventory_management/substance/form.html",
        "update": "inventory_management/substance/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "id"

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, but only admins can register or edit substances
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        return bool(user and user.is_staff)

    post_data_mappings = {
        # a multiselect, so a single selected type must still give a list
        "stereochem_type": list[str],
    }

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Substance) -> dict:
        limit = 25

        # entries in third-party datasets (only those from installed apps)
        linked_datasets = []
        for relation in Substance.linked_dataset_relations:
            table = relation.related_model
            entries = table.objects.filter(substance_id=table_entry.id)
            count = entries.count()
            linked_datasets.append(
                {
                    "label": table.table_label,
                    "table_name": table.table_name,
                    "entries": entries.only("id").order_by("id")[:limit],
                    "count": count,
                    "truncated": count > limit,
                }
            )
        # datasets with entries first
        linked_datasets.sort(key=lambda d: (not d["count"], d["label"]))

        # physical inventory of the substance, where in-stock batches and
        # containers come first (`is_depleted` is nullable)
        in_stock_first = (F("is_depleted").asc(nulls_first=True), "-id")
        batches = table_entry.batches.all()
        batches__count = batches.count()
        containers = Container.get_web_queryset().filter(batch__substance=table_entry)
        containers__count = containers.count()
        usage_logs = UsageLog.objects.filter(
            source_container__batch__substance=table_entry
        ).select_related("source_container", "user")
        usage_logs__count = usage_logs.count()

        # related substances: the tree of `parent` links, plus the salts and
        # solvates that use this substance as their counterion or solvent
        family_tree = cls.get_family_tree(table_entry)
        children__count = len(table_entry.tree_children) + table_entry.tree_more
        salts = table_entry.salts.order_by("id")
        salts__count = salts.count()
        solvates = table_entry.solvates.order_by("id")
        solvates__count = solvates.count()
        related_substances__count = (
            bool(table_entry.parent_id)
            + children__count
            + bool(table_entry.counterion_id)
            + bool(table_entry.solvent_id)
            + salts__count
            + solvates__count
        )

        # mixtures that contain this substance, along with its role in each
        # and the other substances in them
        mixture_components = (
            table_entry.mixture_components.select_related("mixture")
            .prefetch_related(
                Prefetch(
                    "mixture__components",
                    queryset=MixtureComponent.objects.select_related(
                        "substance"
                    ).order_by("id"),
                )
            )
            .order_by("mixture_id")
        )
        mixtures__count = mixture_components.count()
        mixture_components = list(mixture_components[:limit])
        for part in mixture_components:
            part.other_components = [
                other
                for other in part.mixture.components.all()
                if other.substance_id != table_entry.id
            ]

        projects = table_entry.projects.order_by("name")

        return {
            "viewer_default": cls.get_viewer_default(table_entry),
            "linked_datasets": linked_datasets,
            "linked_datasets__count": sum(d["count"] for d in linked_datasets),
            "batches": batches.order_by(*in_stock_first)[:limit],
            "batches__count": batches__count,
            "batches__truncated": batches__count > limit,
            "containers": containers.order_by(*in_stock_first)[:limit],
            "containers__count": containers__count,
            "containers__truncated": containers__count > limit,
            "usage_logs": usage_logs.order_by("-created_at", "-id")[:limit],
            "usage_logs__count": usage_logs__count,
            "usage_logs__truncated": usage_logs__count > limit,
            "family_tree": family_tree,
            "salts": salts[:limit],
            "salts__count": salts__count,
            "salts__truncated": salts__count > limit,
            "solvates": solvates[:limit],
            "solvates__count": solvates__count,
            "solvates__truncated": solvates__count > limit,
            "show_component_cards": bool(
                table_entry.counterion_id
                or table_entry.solvent_id
                or salts__count
                or solvates__count
            ),
            "related_substances__count": related_substances__count,
            "mixture_components": mixture_components,
            "mixtures__count": mixtures__count,
            "mixtures__truncated": mixtures__count > limit,
            "related__count": related_substances__count + mixtures__count,
            "projects": projects,
            "projects__count": projects.count(),
            "id_changes": list(table_entry.id_changes),
        }

    @staticmethod
    def get_viewer_default(substance: Substance | None) -> str:
        """
        Gives which drawing of a substance is shown first ("2d" or "3d") in
        `for_view/viewer.html`. Crystal types are drawn in 3D by default, and
        everything else in 2D (see `Substance.substance_type`). This only
        matters when the substance has both a molecule and a structure.
        """
        if not substance:
            return "2d"
        is_crystal = (substance.substance_type or "").endswith("_crystal")
        has_structure = bool(substance.structure_id)
        if has_structure and (is_crystal or not substance.molecule_id):
            return "3d"
        return "2d"

    @staticmethod
    def get_family_tree(
        substance: Substance,
        max_depth: int = 3,
        max_nodes: int = 100,
        max_children: int = 25,
    ) -> Substance:
        """
        Builds the tree of `parent` links around a substance, for display.

        The tree starts at the substance's top-most ancestor and follows the
        path down to the substance (leaving out the other children of its
        ancestors), and then gives the substance's own descendants up to
        `max_depth` levels down.

        Each node is a `Substance` with these extra attributes:
            - `tree_children`: the child nodes that are shown
            - `tree_more`: how many of the node's children are not shown
              (e.g. siblings of the path, or those past `max_depth`)
            - `is_current`: whether this is the given substance

        Args:
            substance: The substance to build the tree around.
            max_depth: How many levels of descendants to give.
            max_nodes: The most descendants to give in total.
            max_children: The most children to give for any one node.

        Returns:
            The root node of the tree.
        """
        columns = ["id", "common_name", "substance_type", "parent_id", "is_delisted"]

        # walk up to the root, guarding against accidental cycles
        path = [substance]
        while path[0].parent_id and len(path) <= 10:
            if path[0].parent_id in {node.id for node in path}:
                break
            parent = (
                Substance.objects.only(*columns).filter(id=path[0].parent_id).first()
            )
            if not parent:
                break
            path.insert(0, parent)

        for node in path:
            node.tree_children = []
            node.is_current = node is substance
        for parent, child in pairwise(path):
            parent.tree_children = [child]
        nodes = {node.id: node for node in path}

        # walk down from the substance, one level at a time
        level = [substance]
        for _ in range(max_depth):
            children = (
                Substance.objects.only(*columns)
                .filter(parent_id__in=[node.id for node in level])
                .exclude(id__in=list(nodes))
                .order_by("id")[: max_nodes - len(nodes) + len(path)]
            )
            level = []
            for child in children:
                parent = nodes[child.parent_id]
                if len(parent.tree_children) >= max_children:
                    continue
                child.tree_children = []
                child.is_current = False
                parent.tree_children.append(child)
                nodes[child.id] = child
                level.append(child)
            if not level:
                break

        # count all children, so that we can say how many are not shown
        counts = dict(
            Substance.objects.filter(parent_id__in=list(nodes))
            .values_list("parent_id")
            .annotate(count=Count("id"))
            .order_by()
        )
        for node in nodes.values():
            node.tree_more = counts.get(node.id, 0) - len(node.tree_children)

        return path[0]

    @classmethod
    def get_download_entry(cls, table_entry: Substance, view_format: str):
        # substances link to their molecule and structure rather than storing
        # them, so downloads come from whichever one the format is for
        if view_format in ("sdf", "smiles"):
            return table_entry.molecule
        elif view_format in ("cif", "poscar"):
            return table_entry.structure
        # other formats (e.g. "input") are unclear when both are linked
        return None

    # -------------------------------------------------------------------------

    def mount_for_update(self):
        super().mount_for_update()

        # handle molecule viewer
        molecule_db = self.form_data.get("molecule")
        if molecule_db:
            # check if it's already a toolkit obj or needs conversion
            molecule_toolkit = (
                molecule_db
                if isinstance(molecule_db, ToolkitMolecule)
                else molecule_db.to_toolkit()
            )
            self.js_actions.append(
                {
                    "add_mol_viewer": [
                        f"molecule-{self.component_id}-image",
                        molecule_toolkit.to_sdf(),
                        300,
                        300,
                    ]
                }
            )

        # handle structure viewer
        structure_db = self.form_data.get("structure")
        if structure_db:
            structure_toolkit = (
                structure_db
                if isinstance(structure_db, Structure)
                else structure_db.to_toolkit()
            )
            self.js_actions.append(
                {
                    "add_threejs_render": [
                        f"structure-{self.component_id}-viewer",
                        structure_toolkit.to_threejs_json(),
                    ]
                }
            )

    def unmount_for_create(self):
        super().unmount_for_create()
        self._handle_toolkit_objects()

    def unmount_for_update(self):
        super().unmount_for_update()
        self._handle_toolkit_objects()

    def _handle_toolkit_objects(self):
        # handle molecule
        molecule_toolkit = self.form_data.get("molecule")
        if molecule_toolkit and isinstance(molecule_toolkit, ToolkitMolecule):
            from ..models import Molecule

            inchi_key = molecule_toolkit.to_inchi_key()
            molecule_db, _created = Molecule.objects.get_or_create(
                inchi_key=inchi_key,
                defaults=Molecule.from_toolkit(as_dict=True, molecule=molecule_toolkit),
            )
            self.table_entry.molecule = molecule_db

        # handle structure
        structure_toolkit = self.form_data.get("structure")
        if structure_toolkit and isinstance(structure_toolkit, Structure):
            from ..models import Structure as DBStructure

            # TODO: matching?
            structure_db = DBStructure.objects.create(
                **DBStructure.from_toolkit(as_dict=True, structure=structure_toolkit)
            )
            self.table_entry.structure = structure_db

    def on_change_hook__structure__file(self):
        self.load_structure("structure")

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        # most inputs for substance are optional, ID is generated automatically
        "substance_type",
    ]

    def check_form_for_create(self):
        super().check_form_for_create()
        # id is auto-generated in postsave_to_db or handled manually if not set
        if not self.form_data.get("id"):
            self.form_data["id"] = Substance.generate_unique_id()
        if not self.form_data.get("check_digit") and Substance.validate_id(
            self.form_data["id"]
        ):
            self.form_data["check_digit"] = Substance.calculate_check_digit(
                self.form_data["id"]
            )

        # also set registered_by to current user
        if not self.form_data.get("registered_by_id"):
            self.form_data["registered_by_id"] = self.request.user.id

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "substance_type",
        "description",
        "is_theoretical",
        "is_delisted",
        "is_private",
        "is_unknown",
        "common_name",
        "iupac_name",
        "synonyms",
        "molecule",
        "structure",
        "is_primary",
        "parent",
        "counterion",
        "solvent",
        "is_metastable",
        "stereochem_type",
        "extra_metadata",
    ]
