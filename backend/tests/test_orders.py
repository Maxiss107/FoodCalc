import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError

from apps.orders.models import Order, OrderItem
from apps.orders.schemas import (
    OrderCreateSchema,
    OrderOut,
    RecipeSnapshotSchema,
    SnapshotIngredientSchema,
)

User = get_user_model()


def _create_user():
    return User.objects.create_user(email="baker@example.com", password="Password123!")


def _recipe_snapshot() -> dict:
    return {
        "title": "Медовик",
        "output_weight": Decimal("1000.00"),
        "total_cost": Decimal("195.00"),
        "ingredients": [
            {
                "name": "Сливки",
                "amount": Decimal("250.00"),
                "unit": "g",
                "package_weight": Decimal("500.00"),
                "purchase_price": Decimal("390.00"),
                "cost": Decimal("195.00"),
            }
        ],
    }


@pytest.mark.django_db
def test_create_order_with_defaults():
    """Проверяем создание заказа: UUID, владелец, статус NEW и Decimal-цена."""
    owner = _create_user()
    order = Order.objects.create(customer_name="Торт на день рождения", owner=owner)

    assert isinstance(order.id, uuid.UUID)
    assert order.owner == owner
    assert order.status == Order.Status.NEW
    assert order.total_price == Decimal("0.00")
    assert str(order) == "Торт на день рождения"


@pytest.mark.django_db
def test_full_clean_rejects_negative_prices():
    """Проверяем, что full_clean отклоняет отрицательные цены заказа и позиции."""
    owner = _create_user()

    with pytest.raises(DjangoValidationError):
        Order(
            customer_name="Торт на день рождения",
            owner=owner,
            total_price=Decimal("-0.01"),
        ).full_clean()

    order = Order.objects.create(customer_name="Торт на день рождения", owner=owner)
    item = OrderItem(
        order=order,
        recipe_title_snapshot="Медовик",
        unit_cost_snapshot=Decimal("-0.01"),
    )
    with pytest.raises(DjangoValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_order_item_snapshot_keeps_original_data():
    """Проверяем, что слепок рецепта не меняется вместе с исходным словарём."""
    order = Order.objects.create(customer_name="Торт на день рождения", owner=_create_user())
    recipe = _recipe_snapshot()
    item = OrderItem.objects.create(
        order=order,
        recipe_title_snapshot=recipe["title"],
        unit_cost_snapshot=Decimal("12.05"),
        recipe_snapshot=recipe,
    )

    recipe["title"] = "Наполеон"
    recipe["ingredients"][0]["amount"] = Decimal("999.00")
    item.refresh_from_db()

    assert item.recipe_title_snapshot == "Медовик"
    assert item.recipe_snapshot["title"] == "Медовик"
    assert item.recipe_snapshot["total_cost"] == "195.00"
    assert item.recipe_snapshot["ingredients"][0]["name"] == "Сливки"
    assert item.recipe_snapshot["ingredients"][0]["amount"] == "250.00"
    assert item.recipe_snapshot["ingredients"][0]["purchase_price"] == "390.00"


def test_recipe_snapshot_schema_validation():
    """Проверяем валидацию RecipeSnapshotSchema и значения по умолчанию."""
    payload = _recipe_snapshot()
    payload["recipe_id"] = str(uuid.uuid4())
    snapshot = RecipeSnapshotSchema(**payload)

    assert isinstance(snapshot.recipe_id, uuid.UUID)
    assert snapshot.ingredients[0].unit == "g"
    assert snapshot.ingredients[0].amount == Decimal("250.00")

    with pytest.raises(ValidationError):
        RecipeSnapshotSchema(title="", total_cost=Decimal("10.00"))


@pytest.mark.parametrize(
    "amount, purchase_price",
    [(Decimal("0"), Decimal("390")), (Decimal("250"), Decimal("-1"))],
)
def test_snapshot_ingredient_rejects_zero_amount_and_negative_price(amount, purchase_price):
    """Проверяем, что нулевая граммовка и отрицательная цена отклоняются."""
    with pytest.raises(ValidationError):
        SnapshotIngredientSchema(
            name="Сливки",
            amount=amount,
            package_weight=Decimal("500"),
            purchase_price=purchase_price,
            cost=Decimal("195"),
        )


def test_order_create_schema_validation():
    """Проверяем OrderCreateSchema: значения по умолчанию и отрицательная цена."""
    schema = OrderCreateSchema(customer_name="Торт на день рождения")
    assert schema.total_price == Decimal("0.00")
    assert schema.items == []

    schema = OrderCreateSchema(
        customer_name="Торт на день рождения",
        items=[{"recipe_id": uuid.uuid4()}],
    )
    assert len(schema.items) == 1

    with pytest.raises(ValidationError):
        OrderCreateSchema(customer_name="Торт на день рождения", total_price=Decimal("-1.00"))


@pytest.mark.django_db
def test_order_out_serializes_order_with_items():
    """Проверяем сериализацию реального заказа с позицией через OrderOut."""
    order = Order.objects.create(
        customer_name="Торт на день рождения",
        owner=_create_user(),
        total_price=Decimal("195.00"),
    )
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Медовик",
        unit_cost_snapshot=Decimal("12.05"),
        recipe_snapshot=_recipe_snapshot(),
    )
    order = Order.objects.get(pk=order.pk)

    data = OrderOut.from_orm(order)

    assert data.customer_name == "Торт на день рождения"
    assert data.status == "new"
    assert data.total_price == Decimal("195.00")
    assert data.owner_id == order.owner_id
    assert len(data.items) == 1
    assert data.items[0].recipe_title_snapshot == "Медовик"
    assert data.items[0].unit_cost_snapshot == Decimal("12.05")

    snapshot = data.items[0].recipe_snapshot
    assert snapshot["title"] == "Медовик"
    assert snapshot["ingredients"][0]["amount"] == "250.00"
