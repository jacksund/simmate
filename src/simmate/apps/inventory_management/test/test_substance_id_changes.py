import pytest
from django.urls import reverse

from simmate.apps.chembl.models import ChemblMolecule
from simmate.apps.inventory_management.datastores import SubstanceDatastore
from simmate.apps.inventory_management.models import (
    Batch,
    Mixture,
    Substance,
    SubstanceIdChange,
)


@pytest.mark.django_db
def test_merge(admin_client):
    keep = Substance.objects.create(id="BCD-012-3456")
    dup1 = Substance.objects.create(id="BCD-012-0001", parent=keep)
    dup2 = Substance.objects.create(id="BCD-012-0002")
    child = Substance.objects.create(id="BCD-012-0003", parent=dup1)
    batch = Batch.objects.create(is_mixture=False, substance=dup1)
    chembl = ChemblMolecule.objects.create(id=1, substance=dup2)
    mixture = Mixture.objects.create()
    mixture.substances.add(keep, dup1, dup2)

    Substance.merge([dup1.id, dup2.id], into=keep.id, reason="tautomers")

    # links are moved to the kept substance
    batch.refresh_from_db()
    assert batch.substance_id == keep.id
    chembl.refresh_from_db()
    assert chembl.substance_id == keep.id
    child.refresh_from_db()
    assert child.parent_id == keep.id
    assert list(mixture.substances.values_list("id", flat=True)) == [keep.id]

    # duplicates are kept as tombstones that redirect
    for dup in (dup1, dup2):
        dup.refresh_from_db()
        assert dup.is_delisted
        assert dup.replaced_by_id == keep.id
        assert Substance.resolve_id(dup.id) == keep.id
    keep.refresh_from_db()
    assert not keep.is_delisted
    assert keep.parent_id is None
    assert Substance.resolve_id(keep.id) == keep.id

    assert SubstanceIdChange.objects.filter(change_type="merge").count() == 2
    assert keep.id_changes.count() == 2

    # the retired page links to its replacement
    url = reverse("data_explorer:table-entry", args=[Substance.table_name, dup1.id])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert "This ID has been retired" in response.content.decode()

    # delisted substances can't be merged again
    with pytest.raises(ValueError):
        Substance.merge([dup1.id], into=keep.id)


@pytest.mark.django_db
def test_promote():
    old = Substance.objects.create(id="BCD-FGH-3456", common_name="caffeine")
    batch = Batch.objects.create(is_mixture=False, substance=old)
    merged = Substance.objects.create(
        id="BCD-FGH-0001", is_delisted=True, replaced_by=old
    )

    new_id = Substance.promote(old.id, level=1)

    assert Substance.get_id_level(new_id) == 1
    new = Substance.objects.get(id=new_id)
    assert new.common_name == "caffeine"
    assert Substance.validate_id(new.id, new.check_digit)
    batch.refresh_from_db()
    assert batch.substance_id == new_id

    old.refresh_from_db()
    assert old.is_delisted and old.replaced_by_id == new_id
    # older redirects are updated so there is never a chain
    merged.refresh_from_db()
    assert merged.replaced_by_id == new_id

    change = SubstanceIdChange.objects.get(change_type="promote")
    assert (change.old_id, change.new_id) == (old.id, new_id)

    with pytest.raises(ValueError):
        Substance.promote(new_id, level=1)


@pytest.mark.django_db
def test_split():
    flat_id = SubstanceDatastore.get_or_create_id("CC(O)C(=O)O")  # lactic acid
    batch = Batch.objects.create(is_mixture=False, substance_id=flat_id)

    new_ids = Substance.split(
        flat_id,
        [dict(molecule="C[C@H](O)C(=O)O"), dict(molecule="C[C@@H](O)C(=O)O")],
    )

    assert len(set(new_ids)) == 2 and flat_id not in new_ids
    for new_id in new_ids:
        assert Substance.objects.get(id=new_id).parent_id == flat_id

    # the original is kept and nothing is moved
    assert not Substance.objects.get(id=flat_id).is_delisted
    batch.refresh_from_db()
    assert batch.substance_id == flat_id
    assert SubstanceIdChange.objects.filter(change_type="split").count() == 2


@pytest.mark.django_db
def test_delist():
    substance = Substance.objects.create(id="BCD-012-3456")
    Substance.delist(substance.id, reason="typo")
    substance.refresh_from_db()
    assert substance.is_delisted and substance.replaced_by_id is None
    assert SubstanceIdChange.objects.get().change_type == "delist"
