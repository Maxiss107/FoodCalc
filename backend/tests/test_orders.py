import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError

from apps.orders.models import Order, OrderItem
from apps.orders.schemas import OrderCreateSchema, OrderOut, PlanFactInSchema
from apps.orders.services import calculate_plan_fact
from apps.recipes.schemas import RecipeSnapshotSchema

User = get_user_model()


def _create_user():
    return User.objects.create_user(email="baker@example.com", password="Password123!")


def _recipe_snapshot() -> dict:
    return {
        "recipe_id": str(uuid.uuid4()),
        "name": "Медовик",
        "is_semi_finished": False,
        "instructions": "Испечь коржи и прослоить кремом.",
        "total_weight": "1000.00",
        "base_cost": "195.00",
        "safety_margin_percent": "10.00",
        "planned_cost": "214.50",
        "nutrition_total": {
            "calories": "3000.00",
            "proteins": "40.00",
            "fats": "120.00",
            "carbs": "380.00",
        },
        "nutrition_per_100g": {
            "calories": "300.00",
            "proteins": "4.00",
            "fats": "12.00",
            "carbs": "38.00",
        },
        "items": [
            {
                "ingredient_id": str(uuid.uuid4()),
                "ingredient_name": "Сливки",
                "amount_grams": "250.00",
                "purchase_price": "390.00",
                "package_weight": "500.00",
                "item_cost": "195.00",
            }
        ],
    }


@pytest.mark.django_db
def test_create_order_with_defaults():
    owner = _create_user()
    order = Order.objects.create(customer_name="Торт на день рождения", owner=owner)

    assert isinstance(order.id, uuid.UUID)
    assert order.owner == owner
    assert order.status == Order.Status.NEW
    assert order.total_price == Decimal("0.00")
    assert order.actual_cost is None
    assert order.actual_time_minutes is None
    assert str(order) == "Торт на день рождения"


@pytest.mark.django_db
def test_planned_cost_sums_unit_cost_snapshots():
    order = Order.objects.create(customer_name="Торт", owner=_create_user())
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Медовик",
        unit_cost_snapshot=Decimal("12.05"),
    )
    OrderItem.objects.create(
        order=order,
        recipe_title_snapshot="Наполеон",
        unit_cost_snapshot=Decimal("7.95"),
    )

    assert order.planned_cost == Decimal("20.00")


@pytest.mark.django_db
def test_planned_cost_is_zero_without_items():
    order = Order.objects.create(customer_name="Пустой заказ", owner=_create_user())

    assert order.planned_cost == Decimal("0.00")


@pytest.mark.django_db
def test_full_clean_rejects_negative_prices():
    owner = _create_user()

    with pytest.raises(DjangoValidationError):
        Order(
            customer_name="Торт на день рождения",
            owner=owner,
            total_price=Decimal("-0.01"),
        ).full_clean()

    with pytest.raises(DjangoValidationError):
        Order(
            customer_name="Торт на день рождения",
            owner=owner,
            actual_cost=Decimal("-0.01"),
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
    order = Order.objects.create(customer_name="Торт на день рождения", owner=_create_user())
    snapshot = _recipe_snapshot()
    item = OrderItem.objects.create(
        order=order,
        recipe_title_snapshot=snapshot["name"],
        unit_cost_snapshot=Decimal("12.05"),
        recipe_snapshot=snapshot,
    )

    snapshot["name"] = "Наполеон"
    snapshot["items"][0]["amount_grams"] = "999.00"
    item.refresh_from_db()

    assert item.recipe_title_snapshot == "Медовик"
    assert item.recipe_snapshot["name"] == "Медовик"
    assert item.recipe_snapshot["base_cost"] == "195.00"
    assert item.recipe_snapshot["items"][0]["ingredient_name"] == "Сливки"
    assert item.recipe_snapshot["items"][0]["amount_grams"] == "250.00"
    assert item.recipe_snapshot["items"][0]["purchase_price"] == "390.00"


def test_recipe_snapshot_schema_validation():
    snapshot = RecipeSnapshotSchema(**_recipe_snapshot())

    assert isinstance(snapshot.recipe_id, uuid.UUID)
    assert snapshot.name == "Медовик"
    assert snapshot.planned_cost == Decimal("214.50")
    assert snapshot.items[0].amount_grams == Decimal("250.00")
    assert snapshot.nutrition_per_100g.calories == Decimal("300.00")

    with pytest.raises(ValidationError):
        RecipeSnapshotSchema(name="", base_cost=Decimal("10.00"))


def test_order_create_schema_validation():
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


def test_plan_fact_schema_rejects_negative_values():
    with pytest.raises(ValidationError):
        PlanFactInSchema(actual_cost=Decimal("-0.01"), actual_time_minutes=10)

    with pytest.raises(ValidationError):
        PlanFactInSchema(actual_cost=Decimal("10.00"), actual_time_minutes=-1)


@pytest.mark.django_db
def test_order_out_serializes_order_with_items():
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
    assert data.planned_cost == Decimal("12.05")
    assert data.actual_cost is None
    assert data.actual_time_minutes is None
    assert data.owner_id == order.owner_id
    assert len(data.items) == 1
    assert data.items[0].recipe_title_snapshot == "Медовик"
    assert data.items[0].unit_cost_snapshot == Decimal("12.05")

    snapshot = data.items[0].recipe_snapshot
    assert snapshot["name"] == "Медовик"
    assert snapshot["items"][0]["amount_grams"] == "250.00"


def test_calculate_plan_fact_overrun():
    result = calculate_plan_fact(
        order_price=Decimal("100.00"),
        planned_cost=Decimal("40.00"),
        actual_cost=Decimal("55.50"),
        actual_time_minutes=90,
    )

    assert result["cost_deviation"] == Decimal("15.50")
    assert result["planned_profit"] == Decimal("60.00")
    assert result["actual_profit"] == Decimal("44.50")
    assert result["hourly_rate"] == Decimal("29.67")


def test_calculate_plan_fact_saving():
    result = calculate_plan_fact(
        order_price=Decimal("100.00"),
        planned_cost=Decimal("40.00"),
        actual_cost=Decimal("30.00"),
        actual_time_minutes=60,
    )

    assert result["cost_deviation"] == Decimal("-10.00")
    assert result["actual_profit"] == Decimal("70.00")
    assert result["hourly_rate"] == Decimal("70.00")


def test_calculate_plan_fact_zero_minutes_has_no_hourly_rate():
    result = calculate_plan_fact(
        order_price=Decimal("100.00"),
        planned_cost=Decimal("40.00"),
        actual_cost=Decimal("40.00"),
        actual_time_minutes=0,
    )

    assert result["hourly_rate"] is None
    assert result["actual_profit"] == Decimal("60.00")


def test_calculate_plan_fact_rounds_to_two_places():
    result = calculate_plan_fact(
        order_price=Decimal("100.00"),
        planned_cost=Decimal("33.33"),
        actual_cost=Decimal("33.34"),
        actual_time_minutes=7,
    )

    assert result["cost_deviation"] == Decimal("0.01")
    assert result["planned_profit"] == Decimal("66.67")
    assert result["actual_profit"] == Decimal("66.66")
    assert result["hourly_rate"] == Decimal("571.37")
