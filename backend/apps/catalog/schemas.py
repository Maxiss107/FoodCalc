from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator


class IngredientCreateSchema(Schema):
    """
    Pydantic-схема для создания нового ингредиента в каталоге пользователя.

    Обязательными являются название, цена закупки и вес упаковки.
    Текущий остаток на складе и показатели КБЖУ на 100 г имеют значения
    по умолчанию (0.00), что позволяет создавать позицию через быструю
    форму из четырех полей.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название ингредиента",
    )
    purchase_price: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Цена закупки за упаковку",
    )
    package_weight: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Вес (объем) одной упаковки в граммах",
    )
    stock_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Текущий остаток на кухне в граммах",
    )

    calories: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=7,
        decimal_places=2,
        description="Калорийность на 100 г (ккал)",
    )
    proteins: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Белки на 100 г (г)",
    )
    fats: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Жиры на 100 г (г)",
    )
    carbs: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Углеводы на 100 г (г)",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        """Удаляет пробелы по краям и запрещает пустое название."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Ingredient name cannot be blank.")
        return cleaned


class IngredientUpdateSchema(Schema):
    """
    Pydantic-схема для частичного обновления (PATCH) карточки ингредиента.
    Используется для быстрой правки цены, остатка на складе или КБЖУ.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Название ингредиента",
    )
    purchase_price: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Цена закупки за упаковку",
    )
    package_weight: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Вес одной упаковки в граммах",
    )
    stock_amount: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Текущий остаток на кухне в граммах",
    )
    calories: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=7,
        decimal_places=2,
        description="Калорийность на 100 г (ккал)",
    )
    proteins: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Белки на 100 г (г)",
    )
    fats: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Жиры на 100 г (г)",
    )
    carbs: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        max_digits=6,
        decimal_places=2,
        description="Углеводы на 100 г (г)",
    )

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        """Проверяет, что при передаче нового названия оно не состоит только из пробелов."""
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Ingredient name cannot be blank.")
            return cleaned
        return value


class IngredientOutSchema(Schema):
    """
    Pydantic-схема для сериализации карточки ингредиента в ответах API.
    Включает расчетное поле price_per_gram из ORM-модели Ingredient.
    """

    id: UUID
    owner_id: UUID
    name: str
    purchase_price: Decimal
    package_weight: Decimal
    stock_amount: Decimal
    price_per_gram: Decimal
    calories: Decimal
    proteins: Decimal
    fats: Decimal
    carbs: Decimal
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_price_per_gram(obj: Any) -> Decimal:
        return obj.price_per_gram.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
