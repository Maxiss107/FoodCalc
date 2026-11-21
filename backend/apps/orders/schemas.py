from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from ninja import Field, Schema

from apps.orders.models import Order


class SnapshotIngredientSchema(Schema):
    ingredient_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    unit: str = Field(default="g", max_length=20)
    package_weight: Decimal = Field(gt=0)
    purchase_price: Decimal = Field(ge=0)
    cost: Decimal = Field(ge=0)


class RecipeSnapshotSchema(Schema):
    recipe_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    output_weight: Decimal | None = Field(default=None, gt=0)
    total_cost: Decimal = Field(ge=0)
    ingredients: list[SnapshotIngredientSchema] = Field(default_factory=list)


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


class OrderOut(Schema):
    id: UUID
    owner_id: UUID
    customer_name: str
    total_price: Decimal
    status: str
    items: list[OrderItemOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
