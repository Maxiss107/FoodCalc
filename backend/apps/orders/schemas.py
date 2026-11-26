from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from ninja import Field, Schema

from apps.orders.models import Order
from apps.recipes.schemas import RecipeSnapshotSchema


class OrderItemCreateSchema(Schema):
    recipe_id: UUID


class OrderItemOut(Schema):
    id: UUID
    recipe_id: UUID | None = None
    recipe_title_snapshot: str
    unit_cost_snapshot: Decimal
    recipe_snapshot: RecipeSnapshotSchema | dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OrderCreateSchema(Schema):
    customer_name: str = Field(min_length=1, max_length=255)
    total_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    items: list[OrderItemCreateSchema] = Field(default_factory=list)


class OrderUpdateSchema(Schema):
    customer_name: str | None = Field(default=None, min_length=1, max_length=255)
    total_price: Decimal | None = Field(default=None, ge=0)
    status: Order.Status | None = None


class OrderStatusUpdateSchema(Schema):
    status: Order.Status


class OrderOut(Schema):
    id: UUID
    owner_id: UUID
    customer_name: str
    total_price: Decimal
    planned_cost: Decimal
    actual_cost: Decimal | None = None
    actual_time_minutes: int | None = None
    status: str
    items: list[OrderItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShoppingStatus(StrEnum):
    IN_STOCK = "in_stock"
    PARTIAL = "partial"
    OUT_OF_STOCK = "out_of_stock"


class ShoppingOverrideItemSchema(Schema):
    ingredient_id: UUID
    required_grams: Decimal | None = Field(default=None, gt=0)
    package_weight: Decimal | None = Field(default=None, gt=0)
    purchase_price: Decimal | None = Field(default=None, ge=0)


class ShoppingCalcRequestSchema(Schema):
    overrides: list[ShoppingOverrideItemSchema] = Field(default_factory=list)


class ShoppingListItemOut(Schema):
    ingredient_id: UUID | None = None
    ingredient_name: str
    required_grams: Decimal
    stock_amount: Decimal
    deficit_grams: Decimal
    status: ShoppingStatus
    status_label: str
    package_weight: Decimal
    purchase_price: Decimal
    packs_to_buy: int
    leftover_grams: Decimal
    estimated_cost: Decimal


class ShoppingListOut(Schema):
    order_id: UUID
    customer_name: str
    items: list[ShoppingListItemOut] = Field(default_factory=list)
    total_estimated_cost: Decimal


class PlanFactInSchema(Schema):
    actual_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    actual_time_minutes: int = Field(ge=0)


class PlanFactOutSchema(Schema):
    order_id: UUID
    order_price: Decimal
    planned_cost: Decimal
    actual_cost: Decimal
    actual_time_minutes: int
    cost_deviation: Decimal
    planned_profit: Decimal
    actual_profit: Decimal
    hourly_rate: Decimal | None = None
