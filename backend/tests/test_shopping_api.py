import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.services import get_tokens_for_user
from apps.catalog.models import Ingredient
from apps.orders.models import Order, OrderItem
from apps.orders.schemas import ShoppingStatus

User = get_user_model()

WRITE_SQL_PREFIXES = ("INSERT", "UPDATE", "DELETE")


def _auth_headers(user) -> dict[str, str]:
    """Возвращает заголовок Authorization с валидным Bearer access-токеном пользователя."""
    tokens = get_tokens_for_user(user)
    access = tokens["access"] if isinstance(tokens, dict) else tokens.access
    return {"HTTP_AUTHORIZATION": f"Bearer {access}"}


def _make_snapshot(ingredients: list[tuple[Ingredient, Decimal]]) -> dict:
    """Формирует тестовый словарь recipe_snapshot в формате Recipe.to_snapshot() для списка ингредиентов."""
    return {
        "recipe_id": None,
        "name": "Медовик",
        "items": [
            {
                "ingredient_id": str(ing.id),
                "ingredient_name": ing.name,
                "amount_grams": str(amount),
                "package_weight": str(ing.package_weight),
                "purchase_price": str(ing.purchase_price),
                "item_cost": "0.00",
            }
            for ing, amount in ingredients
        ],
    }


@pytest.mark.django_db
def test_shopping_list_three_deficit_scenarios_without_db_write(client):
    """Проверяет 3 статуса дефицита, расчёт целых пачек, required_grams и отсутствие SQL-запросов на запись."""
    user = User.objects.create_user(email="chef@example.com", password="Password123!")

    flour = Ingredient.objects.create(
        owner=user,
        name="Мука",
        purchase_price=Decimal("100.00"),
        package_weight=Decimal("1000.00"),
        stock_amount=Decimal("600.00"),
    )
    cream = Ingredient.objects.create(
        owner=user,
        name="Сливки",
        purchase_price=Decimal("400.00"),
        package_weight=Decimal("500.00"),
        stock_amount=Decimal("100.00"),
    )
    honey = Ingredient.objects.create(
        owner=user,
        name="Мёд",
        purchase_price=Decimal("500.00"),
        package_weight=Decimal("500.00"),
        stock_amount=Decimal("0.00"),
    )

    order = Order.objects.create(owner=user, customer_name="Заказ #1")
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Медовик",
        recipe_snapshot=_make_snapshot(
            [
                (flour, Decimal("500.00")),
                (cream, Decimal("250.00")),
                (honey, Decimal("200.00")),
            ]
        ),
    )

    with CaptureQueriesContext(connection) as queries:
        response = client.post(
            f"/api/orders/{order.id}/shopping-list",
            data=json.dumps({}),
            content_type="application/json",
            **_auth_headers(user),
        )

    write_queries = [
        q["sql"] for q in queries if q["sql"].lstrip().upper().startswith(WRITE_SQL_PREFIXES)
    ]
    assert write_queries == []

    assert response.status_code == 200
    body = response.json()
    items_by_name = {item["ingredient_name"]: item for item in body["items"]}

    assert items_by_name["Мука"]["status"] == ShoppingStatus.IN_STOCK
    assert Decimal(items_by_name["Мука"]["required_grams"]) == Decimal("500.00")
    assert Decimal(items_by_name["Мука"]["stock_amount"]) == Decimal("600.00")
    assert Decimal(items_by_name["Мука"]["deficit_grams"]) == Decimal("0.00")
    assert items_by_name["Мука"]["packs_to_buy"] == 0
    assert Decimal(items_by_name["Мука"]["leftover_grams"]) == Decimal("0.00")
    assert Decimal(items_by_name["Мука"]["estimated_cost"]) == Decimal("0.00")

    assert items_by_name["Сливки"]["status"] == ShoppingStatus.PARTIAL
    assert Decimal(items_by_name["Сливки"]["required_grams"]) == Decimal("250.00")
    assert Decimal(items_by_name["Сливки"]["stock_amount"]) == Decimal("100.00")
    assert Decimal(items_by_name["Сливки"]["deficit_grams"]) == Decimal("150.00")
    assert items_by_name["Сливки"]["packs_to_buy"] == 1
    assert Decimal(items_by_name["Сливки"]["leftover_grams"]) == Decimal("350.00")
    assert Decimal(items_by_name["Сливки"]["estimated_cost"]) == Decimal("400.00")

    assert items_by_name["Мёд"]["status"] == ShoppingStatus.OUT_OF_STOCK
    assert Decimal(items_by_name["Мёд"]["required_grams"]) == Decimal("200.00")
    assert Decimal(items_by_name["Мёд"]["stock_amount"]) == Decimal("0.00")
    assert Decimal(items_by_name["Мёд"]["deficit_grams"]) == Decimal("200.00")
    assert items_by_name["Мёд"]["packs_to_buy"] == 1
    assert Decimal(items_by_name["Мёд"]["leftover_grams"]) == Decimal("300.00")
    assert Decimal(items_by_name["Мёд"]["estimated_cost"]) == Decimal("500.00")

    assert Decimal(body["total_estimated_cost"]) == Decimal("900.00")

    flour.refresh_from_db()
    cream.refresh_from_db()
    honey.refresh_from_db()
    assert flour.stock_amount == Decimal("600.00")
    assert cream.stock_amount == Decimal("100.00")
    assert honey.stock_amount == Decimal("0.00")


@pytest.mark.django_db
def test_shopping_list_manual_weight_and_price_overrides(client):
    """Проверяет пересчёт по ручным правкам веса и цены (включая несколько пачек) без изменения каталога в БД."""
    user = User.objects.create_user(email="chef2@example.com", password="Password123!")
    cream = Ingredient.objects.create(
        owner=user,
        name="Сливки",
        purchase_price=Decimal("400.00"),
        package_weight=Decimal("500.00"),
        stock_amount=Decimal("100.00"),
    )
    order = Order.objects.create(owner=user, customer_name="Заказ #2")
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Медовик",
        recipe_snapshot=_make_snapshot([(cream, Decimal("250.00"))]),
    )

    payload = {
        "overrides": [
            {
                "ingredient_id": str(cream.id),
                "required_grams": "1200.00",
                "package_weight": "500.00",
                "purchase_price": "350.00",
            }
        ]
    }

    response = client.post(
        f"/api/orders/{order.id}/shopping-list",
        data=json.dumps(payload),
        content_type="application/json",
        **_auth_headers(user),
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["status"] == ShoppingStatus.PARTIAL
    assert Decimal(item["required_grams"]) == Decimal("1200.00")
    assert Decimal(item["deficit_grams"]) == Decimal("1100.00")
    assert item["packs_to_buy"] == 3
    assert Decimal(item["leftover_grams"]) == Decimal("400.00")
    assert Decimal(item["estimated_cost"]) == Decimal("1050.00")

    cream.refresh_from_db()
    assert cream.package_weight == Decimal("500.00")
    assert cream.purchase_price == Decimal("400.00")
    assert cream.stock_amount == Decimal("100.00")


@pytest.mark.django_db
def test_shopping_list_sums_same_ingredient_across_order_items(client):
    """Проверяет, что одинаковый ингредиент из нескольких позиций заказа суммируется до сравнения со складом."""
    user = User.objects.create_user(email="chef3@example.com", password="Password123!")
    flour = Ingredient.objects.create(
        owner=user,
        name="Мука",
        purchase_price=Decimal("100.00"),
        package_weight=Decimal("1000.00"),
        stock_amount=Decimal("300.00"),
    )
    order = Order.objects.create(owner=user, customer_name="Заказ #3")
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Медовик",
        recipe_snapshot=_make_snapshot([(flour, Decimal("200.00"))]),
    )
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Наполеон",
        recipe_snapshot=_make_snapshot([(flour, Decimal("250.00"))]),
    )

    response = client.post(
        f"/api/orders/{order.id}/shopping-list",
        data=json.dumps({}),
        content_type="application/json",
        **_auth_headers(user),
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert Decimal(item["required_grams"]) == Decimal("450.00")
    assert Decimal(item["deficit_grams"]) == Decimal("150.00")
    assert item["packs_to_buy"] == 1
    assert Decimal(item["leftover_grams"]) == Decimal("850.00")
    assert Decimal(item["estimated_cost"]) == Decimal("100.00")
    assert item["status"] == ShoppingStatus.PARTIAL


@pytest.mark.django_db
def test_shopping_list_invalid_overrides_returns_422(client):
    """Проверяет, что отрицательные вес или цена в overrides отклоняются схемой с кодом 422."""
    user = User.objects.create_user(email="chef4@example.com", password="Password123!")
    cream = Ingredient.objects.create(
        owner=user,
        name="Сливки",
        purchase_price=Decimal("400.00"),
        package_weight=Decimal("500.00"),
        stock_amount=Decimal("100.00"),
    )
    order = Order.objects.create(owner=user, customer_name="Заказ #4")

    payload = {
        "overrides": [
            {
                "ingredient_id": str(cream.id),
                "required_grams": "-10.00",
                "purchase_price": "-5.00",
            }
        ]
    }

    response = client.post(
        f"/api/orders/{order.id}/shopping-list",
        data=json.dumps(payload),
        content_type="application/json",
        **_auth_headers(user),
    )

    assert response.status_code == 422


@pytest.mark.django_db
def test_shopping_list_foreign_order_returns_404(client):
    """Проверяет изоляцию данных: запрос таблицы закупок по чужому заказу возвращает 404."""
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    other = User.objects.create_user(email="other@example.com", password="Password123!")
    order = Order.objects.create(owner=owner, customer_name="Чужой заказ")

    response = client.post(
        f"/api/orders/{order.id}/shopping-list",
        data=json.dumps({}),
        content_type="application/json",
        **_auth_headers(other),
    )

    assert response.status_code == 404
