import json
from decimal import Decimal

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from apps.accounts.models import User
from apps.catalog.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user() -> User:
    return User.objects.create_user(email="chef_recipes@foodcalc.local", password="Password123!")


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = AccessToken.for_user(test_user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def sample_ingredients(test_user: User) -> dict[str, Ingredient]:
    flour = Ingredient.objects.create(
        owner=test_user,
        name="Мука",
        purchase_price=Decimal("100.00"),
        package_weight=Decimal("1000.00"),  # 0.10 руб/г
        calories=Decimal("340.00"),
        proteins=Decimal("10.00"),
        fats=Decimal("1.00"),
        carbs=Decimal("70.00"),
    )
    sugar = Ingredient.objects.create(
        owner=test_user,
        name="Сахар",
        purchase_price=Decimal("80.00"),
        package_weight=Decimal("1000.00"),  # 0.08 руб/г
        calories=Decimal("400.00"),
        proteins=Decimal("0.00"),
        fats=Decimal("0.00"),
        carbs=Decimal("100.00"),
    )
    return {"flour": flour, "sugar": sugar}


def test_create_recipe_with_items_and_calculations(
    client: Client,
    auth_headers: dict[str, str],
    test_user: User,
    sample_ingredients: dict[str, Ingredient],
):
    """Проверяем создание рецепта через POST /api/recipes с составом и авторасчетом."""
    flour = sample_ingredients["flour"]
    sugar = sample_ingredients["sugar"]

    payload = {
        "name": "Простой бисквит",
        "instructions": "Смешать и выпекать.",
        "is_semi_finished": True,
        "output_weight": "300.00",
        "safety_margin_percent": "10.00",
        "items": [
            {"ingredient_id": str(flour.id), "amount_grams": "200.00"},  # 20.00 руб
            {"ingredient_id": str(sugar.id), "amount_grams": "100.00"},  # 8.00 руб
        ],
    }

    response = client.post(
        "/api/recipes",
        data=json.dumps(payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Простой бисквит"
    assert data["base_cost"] == "28.00"
    # с запасом 10%: 28 * 1.1 = 30.80
    assert data["planned_cost"] == "30.80"
    assert data["calculated_weight"] == "300.00"
    assert data["total_weight"] == "300.00"
    assert len(data["items"]) == 2


def test_get_recipe_detail(
    client: Client,
    auth_headers: dict[str, str],
    test_user: User,
    sample_ingredients: dict[str, Ingredient],
):
    """Проверяем GET /api/recipes/{id}."""
    flour = sample_ingredients["flour"]
    recipe = Recipe.objects.create(
        owner=test_user,
        name="Тесто",
        is_semi_finished=True,
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=flour,
        amount_grams=Decimal("100.00"),
    )

    response = client.get(f"/api/recipes/{recipe.id}", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Тесто"
    assert data["base_cost"] == "10.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["ingredient_name"] == "Мука"


def test_recipe_snapshot_endpoint(
    client: Client,
    auth_headers: dict[str, str],
    test_user: User,
    sample_ingredients: dict[str, Ingredient],
):
    """Проверяем GET /api/recipes/{id}/snapshot для интеграции с заказами."""
    sugar = sample_ingredients["sugar"]
    recipe = Recipe.objects.create(
        owner=test_user,
        name="Карамель",
        output_weight=Decimal("100.00"),
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=sugar,
        amount_grams=Decimal("100.00"),
    )

    response = client.get(f"/api/recipes/{recipe.id}/snapshot", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Карамель"
    assert data["base_cost"] == "8.00"
    assert "nutrition_total" in data
    assert "nutrition_per_100g" in data
    assert len(data["items"]) == 1


def test_patch_recipe_items(
    client: Client,
    auth_headers: dict[str, str],
    test_user: User,
    sample_ingredients: dict[str, Ingredient],
):
    """Проверяем замену состава ингредиентов в рецепте через PATCH."""
    flour = sample_ingredients["flour"]
    sugar = sample_ingredients["sugar"]

    recipe = Recipe.objects.create(owner=test_user, name="Кекс")
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount_grams=Decimal("100.00"))

    # Заменяем муку на сахар
    payload = {
        "name": "Сладкий кекс",
        "items": [
            {"ingredient_id": str(sugar.id), "amount_grams": "50.00"},
        ],
    }
    response = client.patch(
        f"/api/recipes/{recipe.id}",
        data=json.dumps(payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Сладкий кекс"
    assert len(data["items"]) == 1
    assert data["items"][0]["ingredient_name"] == "Сахар"
    assert data["base_cost"] == "4.00"


def test_delete_recipe(client: Client, auth_headers: dict[str, str], test_user: User):
    """Проверяем удаление рецепта (204 No Content)."""
    recipe = Recipe.objects.create(owner=test_user, name="На удаление")
    response = client.delete(f"/api/recipes/{recipe.id}", **auth_headers)
    assert response.status_code == 204
    assert not Recipe.objects.filter(id=recipe.id).exists()
