import json
from datetime import timedelta

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_register_success(client: Client) -> None:
    """Успешная регистрация создаёт пользователя с хешированным паролем и возвращает пару токенов."""
    response = client.post(
        "/api/auth/register",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access"]
    assert data["refresh"]

    user = User.objects.get(email="chef@foodcalc.ru")
    assert user.check_password("StrongPassword123")


def test_register_duplicate_email_returns_409(client: Client) -> None:
    """Повторная регистрация уже существующего email (без учёта регистра) возвращает 409."""
    User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")

    response = client.post(
        "/api/auth/register",
        data=json.dumps({"email": "CHEF@foodcalc.ru", "password": "AnotherPassword123"}),
        content_type="application/json",
    )

    assert response.status_code == 409


def test_register_invalid_email_returns_422(client: Client) -> None:
    """Регистрация с некорректным форматом email отклоняется схемой с кодом 422."""
    response = client.post(
        "/api/auth/register",
        data=json.dumps({"email": "not-an-email", "password": "StrongPassword123"}),
        content_type="application/json",
    )

    assert response.status_code == 422


def test_register_short_password_returns_422(client: Client) -> None:
    """Регистрация с паролем короче 8 символов отклоняется схемой с кодом 422."""
    response = client.post(
        "/api/auth/register",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "short"}),
        content_type="application/json",
    )

    assert response.status_code == 422


def test_login_success(client: Client) -> None:
    """Вход с верным email и паролем возвращает 200 и пару JWT-токенов."""
    User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")

    response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access"]
    assert data["refresh"]
    assert data["token_type"] == "bearer"


def test_login_nonexistent_email_returns_401(client: Client) -> None:
    """Вход с email, которого нет в БД, возвращает 401."""
    response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "unknown@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )

    assert response.status_code == 401


def test_login_wrong_password_returns_401(client: Client) -> None:
    """Вход с существующим email, но неверным паролем возвращает 401."""
    User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")

    response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "WrongPassword"}),
        content_type="application/json",
    )

    assert response.status_code == 401


def test_login_inactive_or_system_user_returns_401(client: Client) -> None:
    """Вход для неактивного (is_active=False) или системного (is_system=True) пользователя запрещён (401)."""
    inactive_user = User.objects.create_user(
        email="inactive@foodcalc.ru",
        password="StrongPassword123",
    )
    inactive_user.is_active = False
    inactive_user.save(update_fields=["is_active"])

    inactive_response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "inactive@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )
    assert inactive_response.status_code == 401

    system_user = User.objects.create_user(
        email="system_test@foodcalc.ru",
        password="StrongPassword123",
        is_system=True,
    )
    assert system_user.is_system is True

    system_response = client.post(
        "/api/auth/login",
        data=json.dumps(
            {"email": "system_test@foodcalc.ru", "password": "StrongPassword123"},
        ),
        content_type="application/json",
    )
    assert system_response.status_code == 401


def test_me_with_valid_access_token(client: Client) -> None:
    """Запрос GET /api/auth/me с валидным access-токеном возвращает профиль текущего пользователя."""
    user = User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")
    login_response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )
    access_token = login_response.json()["access"]

    response = client.get(
        "/api/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == "chef@foodcalc.ru"


def test_me_without_token_returns_401(client: Client) -> None:
    """Запрос GET /api/auth/me без заголовка Authorization возвращает 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_returns_401(client: Client) -> None:
    """Запрос GET /api/auth/me с поддельным или повреждённым токеном возвращает 401."""
    response = client.get(
        "/api/auth/me",
        HTTP_AUTHORIZATION="Bearer invalid.token.value",
    )
    assert response.status_code == 401


def test_me_with_refresh_token_instead_of_access_returns_401(client: Client) -> None:
    """Использование refresh-токена вместо access-токена для доступа к /me отклоняется с кодом 401."""
    User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")
    login_response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )
    refresh_token = login_response.json()["refresh"]

    response = client.get(
        "/api/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {refresh_token}",
    )
    assert response.status_code == 401


def test_me_with_expired_access_token_returns_401(client: Client) -> None:
    """Запрос GET /api/auth/me с просроченным access-токеном возвращает 401."""
    user = User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")
    expired_token = AccessToken.for_user(user)
    expired_token.set_exp(lifetime=timedelta(seconds=-1))

    response = client.get(
        "/api/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {expired_token}",
    )
    assert response.status_code == 401


def test_refresh_token_success_and_invalid_cases(client: Client) -> None:
    """Обновление токена успешно с валидным refresh и возвращает 401 для битого токена или access вместо refresh."""
    User.objects.create_user(email="chef@foodcalc.ru", password="StrongPassword123")
    login_response = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "chef@foodcalc.ru", "password": "StrongPassword123"}),
        content_type="application/json",
    )
    access_token = login_response.json()["access"]
    refresh_token = login_response.json()["refresh"]

    ok_response = client.post(
        "/api/auth/refresh",
        data=json.dumps({"refresh": refresh_token}),
        content_type="application/json",
    )
    assert ok_response.status_code == 200
    assert ok_response.json()["access"]

    bad_response = client.post(
        "/api/auth/refresh",
        data=json.dumps({"refresh": "invalid.token.value"}),
        content_type="application/json",
    )
    assert bad_response.status_code == 401

    wrong_type_response = client.post(
        "/api/auth/refresh",
        data=json.dumps({"refresh": access_token}),
        content_type="application/json",
    )
    assert wrong_type_response.status_code == 401
