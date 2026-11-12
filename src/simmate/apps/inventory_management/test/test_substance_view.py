import pytest
from django.urls import reverse

from simmate.apps.inventory_management.models import (
    Batch,
    Container,
    Mixture,
    Molecule,
    Structure,
    Substance,
    UsageLog,
)
from simmate.toolkit import Molecule as ToolkitMolecule


def get_entry(client, substance: Substance, **params):
    url = reverse(
        "data_explorer:table-entry",
        args=[Substance.table_name, substance.id],
    )
    return client.get(url, params)


@pytest.mark.django_db
def test_entry_view(admin_client, sample_structures):
    molecule = Molecule.from_toolkit(molecule=ToolkitMolecule.from_smiles("CCO"))
    molecule.save()
    crystal = sample_structures["C_mp-48_primitive"]
    structure = Structure.from_toolkit(structure=crystal)
    structure.save()

    both = Substance.objects.create(
        id="BCD-012-0001",
        substance_type="molecular_crystal",
        molecule=molecule,
        structure=structure,
    )
    molecule_only = Substance.objects.create(
        id="BCD-012-0002",
        substance_type="molecule",
        molecule=molecule,
    )
    structure_only = Substance.objects.create(
        id="BCD-012-0003",
        substance_type="inorganic_crystal",
        structure=structure,
    )
    neither = Substance.objects.create(id="BCD-012-0004", is_private=True)

    # the 2D/3D toggle is only given when both are linked, and crystals
    # start in 3D
    response = get_entry(admin_client, both)
    assert response.status_code == 200
    assert response.context["viewer_default"] == "3d"
    content = response.content.decode()
    assert 'id="viewer-2d-pane"' in content
    assert 'id="molecule-details-section"' in content
    assert 'id="structure-details-section"' in content

    # inventory of the substance is split into batches, containers, and usage
    batch = Batch.objects.create(is_mixture=False, substance=molecule_only)
    container = Container.objects.create(
        batch=batch,
        initial_amount=10,
        current_amount=9,
        amount_units="g",
    )
    UsageLog.objects.create(source_container=container, amount_removed=1)

    response = get_entry(admin_client, molecule_only)
    assert response.status_code == 200
    assert response.context["viewer_default"] == "2d"
    assert response.context["batches__count"] == 1
    assert response.context["containers__count"] == 1
    assert response.context["usage_logs__count"] == 1
    content = response.content.decode()
    assert 'id="viewer-2d-pane"' not in content
    assert 'id="molecule-details-section"' in content
    assert 'id="structure-details-section"' not in content

    response = get_entry(admin_client, structure_only)
    assert response.status_code == 200
    assert response.context["viewer_default"] == "3d"
    content = response.content.decode()
    assert 'id="molecule-details-section"' not in content
    assert 'id="structure-details-section"' in content

    response = get_entry(admin_client, neither)
    assert response.status_code == 200
    assert "Structure kept private" in response.content.decode()

    # downloads come from the linked molecule or structure
    for view_format in ("sdf", "smiles", "cif", "poscar"):
        assert get_entry(admin_client, both, format=view_format).status_code == 200
    response = get_entry(admin_client, molecule_only, format="smiles")
    assert response.content.decode() == molecule.smiles
    assert get_entry(admin_client, molecule_only, format="cif").status_code == 404
    assert get_entry(admin_client, structure_only, format="sdf").status_code == 404
    # the original input is unclear when both are linked
    assert get_entry(admin_client, both, format="input").status_code == 404


@pytest.mark.django_db
def test_entry_view_related(admin_client):
    acetate = Substance.objects.create(id="BCD-012-0001", common_name="acetate")
    sodium = Substance.objects.create(id="BCD-012-0002", common_name="sodium")
    salt = Substance.objects.create(
        id="BCD-012-0003",
        parent=acetate,
        counterion=sodium,
    )
    hydrate = Substance.objects.create(id="BCD-012-0004", parent=salt)
    Substance.objects.create(id="BCD-012-0005", parent=acetate)
    mixture = Mixture.objects.create()
    mixture.substances.add(salt, sodium)

    # the tree goes from the top-most parent down through the substance to its
    # children, while the parent's other children are only counted
    response = get_entry(admin_client, salt)
    assert response.status_code == 200
    root = response.context["family_tree"]
    assert root.id == acetate.id
    assert root.tree_more == 1
    [node] = root.tree_children
    assert node.id == salt.id
    assert node.is_current
    assert [child.id for child in node.tree_children] == [hydrate.id]
    # the parent, child, and counterion
    assert response.context["related_substances__count"] == 3

    # mixtures give the other substances in them
    [part] = response.context["mixture_components"]
    assert [other.substance_id for other in part.other_components] == [sodium.id]

    # the counterion lists the salts that use it
    response = get_entry(admin_client, sodium)
    assert response.status_code == 200
    assert response.context["salts__count"] == 1
    assert "Counterion in" in response.content.decode()
