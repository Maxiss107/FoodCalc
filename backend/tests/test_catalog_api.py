import json
from decimal import Decimal

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from apps.accounts.models import User
from apps.catalog.models import Ingredient

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user() -> User:
    return User.objects.create_user(email="baker@foodcalc.local", password="Password123!")


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = AccessToken.for_user(test_user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_list_ingredients_empty_and_created(
    client: Client, auth_headers: dict[str, str], test_user: User
):
    """Проверяем получение списка ингредиентов пользователя."""
    response = client.get("/api/catalog/ingredients", **auth_headers)
    assert response.status_code == 200
    assert response.json() == []

    # Создаем личный ингредиент
    Ingredient.objects.create(
        owner=test_user,
        name="Мука пшеничная",
        purchase_price=Decimal("120.00"),
        package_weight=Decimal("1000.00"),
    )

    response = client.get("/api/catalog/ingredients", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Мука пшеничная"
    assert data[0]["price_per_gram"] == "0.12"


def test_list_ingredients_includes_system_templates(client: Client, auth_headers: dict[str, str]):
    """Проверяем, что в списке отображаются и системные шаблоны."""
    system_user = User.objects.get_system_user()
    Ingredient.objects.create(
        owner=system_user,
        name="Сахар системный",
        purchase_price=Decimal("80.00"),
        package_weight=Decimal("1000.00"),
    )

    response = client.get("/api/catalog/ingredients", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert any(item["name"] == "Сахар системный" for item in data)


def test_search_ingredients(client: Client, auth_headers: dict[str, str], test_user: User):
    """Проверяем поиск по названию ингредиента (query param ?q=...)."""
    Ingredient.objects.create(
        owner=test_user,
        name="Шоколад тёмный",
        purchase_price=Decimal("500.00"),
        package_weight=Decimal("500.00"),
    )
    Ingredient.objects.create(
        owner=test_user,
        name="Ваниль",
        purchase_price=Decimal("200.00"),
        package_weight=Decimal("50.00"),
    )

    response = client.get("/api/catalog/ingredients?q=шоколад", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Шоколад тёмный"


def test_create_ingredient_success(client: Client, auth_headers: dict[str, str], test_user: User):
    """Проверяем создание ингредиента через POST /api/catalog/ingredients."""
    payload = {
        "name": "Сливки 33%",
        "purchase_price": "350.00",
        "package_weight": "500.00",
        "stock_amount": "250.00",
        "calories": "322.00",
        "proteins": "2.20",
        "fats": "33.00",
        "carbs": "4.00",
    }
    response = client.post(
        "/api/catalog/ingredients",
        data=json.dumps(payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Сливки 33%"
    assert data["price_per_gram"] == "0.70"
    assert data["owner_id"] == str(test_user.id)


def test_patch_ingredient_stock_and_price(
    client: Client, auth_headers: dict[str, str], test_user: User
):
    """Проверяем быстрое обновление остатка и цены через PATCH."""
    ing = Ingredient.objects.create(
        owner=test_user,
        name="Масло",
        purchase_price=Decimal("180.00"),
        package_weight=Decimal("180.00"),
        stock_amount=Decimal("100.00"),
    )

    patch_payload = {
        "purchase_price": "200.00",
        "stock_amount": "500.00",
    }
    response = client.patch(
        f"/api/catalog/ingredients/{ing.id}",
        data=json.dumps(patch_payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["purchase_price"] == "200.00"
    assert data["stock_amount"] == "500.00"
    assert data["price_per_gram"] == "1.11"


def test_patch_system_template_forbidden(client: Client, auth_headers: dict[str, str]):
    """Запрещено изменять системный шаблон (403 Forbidden)."""
    system_user = User.objects.get_system_user()
    template = Ingredient.objects.create(
        owner=system_user,
        name="Шаблонная мука",
        purchase_price=Decimal("100.00"),
        package_weight=Decimal("1000.00"),
    )

    response = client.patch(
        f"/api/catalog/ingredients/{template.id}",
        data=json.dumps({"purchase_price": "200.00"}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 403


def test_delete_ingredient(client: Client, auth_headers: dict[str, str], test_user: User):
    """Проверяем удаление личного ингредиента (204 No Content)."""
    ing = Ingredient.objects.create(
        owner=test_user,
        name="Удаляемый ингредиент",
        purchase_price=Decimal("50.00"),
        package_weight=Decimal("100.00"),
    )

    response = client.delete(f"/api/catalog/ingredients/{ing.id}", **auth_headers)
    assert response.status_code == 204
    assert not Ingredient.objects.filter(id=ing.id).exists()


def test_copy_template_ingredient(client: Client, auth_headers: dict[str, str], test_user: User):
    """Проверяем копирование системного шаблона на личный склад."""
    system_user = User.objects.get_system_user()
    template = Ingredient.objects.create(
        owner=system_user,
        name="Какао Callebaut",
        purchase_price=Decimal("1200.00"),
        package_weight=Decimal("1000.00"),
        calories=Decimal("380.00"),
    )

    response = client.post(f"/api/catalog/ingredients/{template.id}/copy", **auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] == str(test_user.id)
    assert data["name"] == "Какао Callebaut"
    assert data["id"] != str(template.id)
