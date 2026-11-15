import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_uuid_and_email():
    """Проверяем создание обычного пользователя, нормализацию email и хэш пароля."""
    user = User.objects.create_user(
        email="TestChef@Example.com",
        password="SecretPassword123!",
    )

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "testchef@example.com"
    assert str(user) == "testchef@example.com"
    assert user.password != "SecretPassword123!"
    assert user.check_password("SecretPassword123!") is True
    assert user.is_system is False
    assert user.is_staff is False


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Проверяем, что нельзя создать пользователя с пустым email."""
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="SecretPassword123!")


@pytest.mark.django_db
def test_create_duplicate_email_raises_integrity_error():
    """Проверяем уникальность email в базе данных."""
    User.objects.create_user(email="chef@example.com", password="Password123!")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="chef@example.com", password="AnotherPassword!")


@pytest.mark.django_db
def test_create_superuser_permissions():
    """Проверяем создание суперпользователя и защиту флагов is_staff / is_superuser."""
    admin = User.objects.create_superuser(
        email="admin@foodcalc.local",
        password="AdminPassword123!",
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True

    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="badadmin@foodcalc.local",
            password="AdminPassword123!",
            is_staff=False,
        )


@pytest.mark.django_db
def test_get_system_user_idempotent():
    """Проверяем, что системный пользователь создается один раз и без пароля для входа."""
    sys_user_1 = User.objects.get_system_user()
    sys_user_2 = User.objects.get_system_user()

    assert sys_user_1.id == sys_user_2.id
    assert sys_user_1.is_system is True
    assert sys_user_1.has_usable_password() is False
