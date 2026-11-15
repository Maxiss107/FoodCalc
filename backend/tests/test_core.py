from core.models import CoreModel, OwnedModel


def test_core_and_owned_models_structure():
    """Проверяем структуру абстрактных классов CoreModel и OwnedModel."""
    assert CoreModel._meta.abstract is True
    assert OwnedModel._meta.abstract is True

    id_field = CoreModel._meta.get_field("id")
    assert id_field.primary_key is True

    owner_field = OwnedModel._meta.get_field("owner")
    assert owner_field.null is False
    assert owner_field.remote_field.related_name == "%(class)ss"
