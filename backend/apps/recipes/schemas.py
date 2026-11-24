from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator


class RecipeIngredientCreateSchema(Schema):
    """
    Pydantic-схема позиции состава рецепта при создании или обновлении.
    Связывает выбранный ингредиент из каталога с его граммовкой в блюде.
    """

    ingredient_id: UUID = Field(
        ...,
        description="UUID ингредиента из каталога",
    )
    amount_grams: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Вес ингредиента в рецепте (в граммах)",
    )


class RecipeIngredientOutSchema(Schema):
    """
    Pydantic-схема для вывода позиции состава рецепта в ответах API.
    Содержит расчетную стоимость и КБЖУ для указанной граммовки.
    """

    id: UUID
    ingredient_id: UUID
    ingredient_name: str
    amount_grams: Decimal
    cost: Decimal
    calories: Decimal
    proteins: Decimal
    fats: Decimal
    carbs: Decimal

    @staticmethod
    def resolve_ingredient_name(obj: Any) -> str:
        """Извлекает название ингредиента из связанной модели Ingredient или словаря."""
        if isinstance(obj, dict):
            return str(obj.get("ingredient_name", ""))
        return obj.ingredient.name


class RecipeCreateSchema(Schema):
    """
    Pydantic-схема для создания нового рецепта или полуфабриката вместе с составом.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название рецепта или полуфабриката",
    )
    instructions: str = Field(
        default="",
        description="Пошаговая текстовая инструкция приготовления",
    )
    is_semi_finished: bool = Field(
        default=False,
        description="Флаг полуфабриката (True — полуфабрикат, False — готовое блюдо)",
    )
    output_weight: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Вес готового изделия в граммах (если не указан — сумма ингредиентов)",
    )
    safety_margin_percent: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
        description="Процент запаса от скачков цен на сырье (например, 5-10%)",
    )
    items: list[RecipeIngredientCreateSchema] = Field(
        default_factory=list,
        description="Список ингредиентов рецепта с граммовками",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        """Удаляет пробелы по краям и запрещает пустое название рецепта."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Recipe name cannot be blank.")
        return cleaned

    @field_validator("items")
    @classmethod
    def validate_unique_ingredients(
        cls, value: list[RecipeIngredientCreateSchema]
    ) -> list[RecipeIngredientCreateSchema]:
        """Запрещает дублирование одного и того же ингредиента в рамках одного рецепта."""
        seen_ids = [item.ingredient_id for item in value]
        if len(seen_ids) != len(set(seen_ids)):
            raise ValueError("Duplicate ingredients are not allowed in a single recipe.")
        return value


class RecipeUpdateSchema(Schema):
    """
    Pydantic-схема для частичного обновления (PATCH) карточки рецепта и его состава.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Название рецепта или полуфабриката",
    )
    instructions: str | None = Field(
        default=None,
        description="Пошаговая текстовая инструкция приготовления",
    )
    is_semi_finished: bool | None = Field(
        default=None,
        description="Флаг полуфабриката",
    )
    output_weight: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Вес готового изделия в граммах",
    )
    safety_margin_percent: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
        description="Процент запаса от скачков цен (%)",
    )
    items: list[RecipeIngredientCreateSchema] | None = Field(
        default=None,
        description="Обновленный состав ингредиентов рецепта",
    )

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        """Проверяет, что переданное название не состоит только из пробелов."""
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Recipe name cannot be blank.")
            return cleaned
        return value

    @field_validator("items")
    @classmethod
    def validate_optional_unique_ingredients(
        cls, value: list[RecipeIngredientCreateSchema] | None
    ) -> list[RecipeIngredientCreateSchema] | None:
        """Запрещает дублирование ингредиентов при обновлении состава рецепта."""
        if value is not None:
            seen_ids = [item.ingredient_id for item in value]
            if len(seen_ids) != len(set(seen_ids)):
                raise ValueError("Duplicate ingredients are not allowed in a single recipe.")
        return value


class RecipeOutSchema(Schema):
    """
    Pydantic-схема для сериализации карточки рецепта в ответах API.
    Включает полный блок авторасчета: вес, базовую и плановую себестоимость,
    суммарное КБЖУ, КБЖУ на 100 г и детализированный список ингредиентов.
    """

    id: UUID
    owner_id: UUID
    name: str
    instructions: str
    is_semi_finished: bool
    output_weight: Decimal | None
    calculated_weight: Decimal
    total_weight: Decimal
    base_cost: Decimal
    safety_margin_percent: Decimal
    planned_cost: Decimal
    total_calories: Decimal
    total_proteins: Decimal
    total_fats: Decimal
    total_carbs: Decimal
    calories_per_100g: Decimal
    proteins_per_100g: Decimal
    fats_per_100g: Decimal
    carbs_per_100g: Decimal
    items: list[RecipeIngredientOutSchema]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_items(obj: Any) -> list[Any]:
        """Возвращает список связанных позиций состава рецепта (RecipeIngredient)."""
        if isinstance(obj, dict):
            return obj.get("items", [])
        return obj.items_list


# =====================================================================
# Схемы Snapshot рецепта (для интеграции с заказами в apps/orders)
# =====================================================================


class NutritionSnapshotSchema(Schema):
    """Схема фиксации показателей КБЖУ внутри снимка рецепта."""

    calories: Decimal
    proteins: Decimal
    fats: Decimal
    carbs: Decimal


class RecipeIngredientSnapshotSchema(Schema):
    """
    Схема фиксации параметров одного ингредиента на момент создания заказа.
    Хранит закупочную цену, фасовку и стоимость граммовки в момент сделки.
    """

    ingredient_id: UUID
    ingredient_name: str
    amount_grams: Decimal
    purchase_price: Decimal
    package_weight: Decimal
    item_cost: Decimal


class RecipeSnapshotSchema(Schema):
    """
    Полная схема неизменяемого снимка (snapshot) рецепта для хранения в OrderItem.
    Используется при создании заказа через метод recipe.to_snapshot().
    """

    recipe_id: UUID
    name: str
    is_semi_finished: bool
    instructions: str
    total_weight: Decimal
    base_cost: Decimal
    safety_margin_percent: Decimal
    planned_cost: Decimal
    nutrition_total: NutritionSnapshotSchema
    nutrition_per_100g: NutritionSnapshotSchema
    items: list[RecipeIngredientSnapshotSchema]