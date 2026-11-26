import json
from decimal import Decimal
from uuid import uuid4

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.accounts.services import get_tokens_for_user
from apps.catalog.models import Ingredient
from apps.orders.models import Order
from apps.recipes.models import Recipe, RecipeIngredient

pytestmark = pytest.mark.django_db


@pytest.fixture
def user() -> User:
    return User.objects.create_user(email="chef_orders@foodcalc.local", password="Password123!")


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(email="other_orders@foodcalc.local", password="Password123!")


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    tokens = get_tokens_for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}


def _make_recipe(
    owner: User,
    *,
    name: str = "Бисквит",
    purchase_price: str = "100.00",
    package_weight: str = "1000.00",
    amount_grams: str = "200.00",
    safety_margin_percent: str = "10.00",
) -> tuple[Recipe, Ingredient]:
    ingredient = Ingredient.objects.create(
        owner=owner,
        name="Мука",
        purchase_price=Decimal(purchase_price),
        package_weight=Decimal(package_weight),
    )
    recipe = Recipe.objects.create(
        owner=owner,
        name=name,
        safety_margin_percent=Decimal(safety_margin_percent),
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ingredient,
        amount_grams=Decimal(amount_grams),
    )
    return recipe, ingredient


def _post_order(
    client: Client,
    headers: dict[str, str],
    recipe: Recipe,
    *,
    customer_name: str = "Заказ на торт",
    total_price: str = "100.00",
) -> dict:
    response = client.post(
        "/api/orders",
        data=json.dumps(
            {
                "customer_name": customer_name,
                "total_price": total_price,
                "items": [{"recipe_id": str(recipe.id)}],
            }
        ),
        content_type="application/json",
        **headers,
    )
    assert response.status_code == 201
    return response.json()


def test_orders_require_auth(client: Client) -> None:
    assert client.get("/api/orders").status_code == 401
    assert (
        client.post(
            "/api/orders",
            data=json.dumps({"customer_name": "Заказ"}),
            content_type="application/json",
        ).status_code
        == 401
    )
    assert client.get(f"/api/orders/{uuid4()}").status_code == 401


def test_create_order_freezes_recipe_snapshot(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    recipe, ingredient = _make_recipe(user)

    order = _post_order(client, auth_headers, recipe)

    assert order["planned_cost"] == "22.00"
    assert order["status"] == "new"
    assert len(order["items"]) == 1
    assert order["items"][0]["recipe_id"] == str(recipe.id)
    assert order["items"][0]["recipe_title_snapshot"] == "Бисквит"
    assert order["items"][0]["unit_cost_snapshot"] == "22.00"

    ingredient.purchase_price = Decimal("400.00")
    ingredient.save()

    response = client.get(f"/api/orders/{order['id']}", **auth_headers)
    assert response.status_code == 200
    detail = response.json()

    assert detail["planned_cost"] == "22.00"
    assert detail["items"][0]["unit_cost_snapshot"] == "22.00"

    snapshot = detail["items"][0]["recipe_snapshot"]
    assert snapshot["name"] == "Бисквит"
    assert snapshot["base_cost"] == "20.00"
    assert snapshot["planned_cost"] == "22.00"
    assert snapshot["items"][0]["purchase_price"] == "100.00"


def test_create_order_with_unknown_recipe_returns_404(
    client: Client,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/orders",
        data=json.dumps(
            {
                "customer_name": "Заказ",
                "items": [{"recipe_id": str(uuid4())}],
            }
        ),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Рецепт не найден."


def test_create_order_with_foreign_recipe_returns_404(
    client: Client,
    other_user: User,
    auth_headers: dict[str, str],
) -> None:
    foreign_recipe, _ = _make_recipe(other_user, name="Чужой рецепт")

    response = client.post(
        "/api/orders",
        data=json.dumps(
            {
                "customer_name": "Заказ",
                "items": [{"recipe_id": str(foreign_recipe.id)}],
            }
        ),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 404


def test_list_orders_returns_only_own_and_filters_by_status(
    client: Client,
    user: User,
    other_user: User,
    auth_headers: dict[str, str],
) -> None:
    Order.objects.create(owner=user, customer_name="Новый", status=Order.Status.NEW)
    Order.objects.create(owner=user, customer_name="Готовый", status=Order.Status.DONE)
    Order.objects.create(owner=other_user, customer_name="Чужой", status=Order.Status.NEW)

    response = client.get("/api/orders", **auth_headers)
    assert response.status_code == 200
    names = {item["customer_name"] for item in response.json()}
    assert names == {"Новый", "Готовый"}

    response = client.get("/api/orders?status=done", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_name"] == "Готовый"


def test_patch_status_from_new_to_done(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    order = Order.objects.create(owner=user, customer_name="Заказ")

    response = client.patch(
        f"/api/orders/{order.id}/status",
        data=json.dumps({"status": "done"}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"

    order.refresh_from_db()
    assert order.status == Order.Status.DONE


def test_patch_status_of_foreign_order_returns_404(
    client: Client,
    other_user: User,
    auth_headers: dict[str, str],
) -> None:
    order = Order.objects.create(owner=other_user, customer_name="Чужой заказ")

    response = client.patch(
        f"/api/orders/{order.id}/status",
        data=json.dumps({"status": "done"}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 404


def test_plan_fact_overrun_is_saved(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    recipe, _ = _make_recipe(user)
    order = _post_order(client, auth_headers, recipe)

    response = client.post(
        f"/api/orders/{order['id']}/plan-fact",
        data=json.dumps({"actual_cost": "30.00", "actual_time_minutes": 60}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order["id"]
    assert data["order_price"] == "100.00"
    assert data["planned_cost"] == "22.00"
    assert data["actual_cost"] == "30.00"
    assert data["actual_time_minutes"] == 60
    assert data["cost_deviation"] == "8.00"
    assert data["planned_profit"] == "78.00"
    assert data["actual_profit"] == "70.00"
    assert data["hourly_rate"] == "70.00"

    saved = Order.objects.get(id=order["id"])
    assert saved.actual_cost == Decimal("30.00")
    assert saved.actual_time_minutes == 60

    detail = client.get(f"/api/orders/{order['id']}", **auth_headers).json()
    assert detail["actual_cost"] == "30.00"
    assert detail["actual_time_minutes"] == 60


def test_plan_fact_saving_shows_negative_deviation(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    recipe, _ = _make_recipe(user)
    order = _post_order(client, auth_headers, recipe)

    response = client.post(
        f"/api/orders/{order['id']}/plan-fact",
        data=json.dumps({"actual_cost": "10.00", "actual_time_minutes": 120}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cost_deviation"] == "-12.00"
    assert data["planned_profit"] == "78.00"
    assert data["actual_profit"] == "90.00"
    assert data["hourly_rate"] == "45.00"


def test_plan_fact_without_time_has_no_hourly_rate(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    recipe, _ = _make_recipe(user)
    order = _post_order(client, auth_headers, recipe)

    response = client.post(
        f"/api/orders/{order['id']}/plan-fact",
        data=json.dumps({"actual_cost": "22.00", "actual_time_minutes": 0}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["hourly_rate"] is None
    assert data["actual_profit"] == "78.00"


def test_plan_fact_with_negative_cost_returns_422(
    client: Client,
    user: User,
    auth_headers: dict[str, str],
) -> None:
    recipe, _ = _make_recipe(user)
    order = _post_order(client, auth_headers, recipe)

    response = client.post(
        f"/api/orders/{order['id']}/plan-fact",
        data=json.dumps({"actual_cost": "-1.00", "actual_time_minutes": 60}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 422


def test_plan_fact_of_foreign_order_returns_404(
    client: Client,
    other_user: User,
    auth_headers: dict[str, str],
) -> None:
    order = Order.objects.create(owner=other_user, customer_name="Чужой заказ")

    response = client.post(
        f"/api/orders/{order.id}/plan-fact",
        data=json.dumps({"actual_cost": "10.00", "actual_time_minutes": 10}),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 404
