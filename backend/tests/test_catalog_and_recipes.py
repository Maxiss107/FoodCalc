import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from pydantic import ValidationError

from apps.catalog.models import Ingredient
from apps.catalog.schemas import IngredientCreateSchema, IngredientOutSchema
from apps.recipes.models import Recipe, RecipeIngredient
from apps.recipes.schemas import (
    RecipeCreateSchema,
    RecipeOutSchema,
    RecipeSnapshotSchema,
)

User = get_user_model()


@pytest.mark.django_db
def test_create_ingredient_and_price_per_gram():
    """Проверяем создание ингредиента, дефолтные поля КБЖУ и расчет цены за 1 грамм."""
    user = User.objects.create_user(email="baker@foodcalc.local", password="Password123!")

    ingredient = Ingredient.objects.create(
        owner=user,
        name="Пшеничная мука",
        purchase_price=Decimal("120.00"),
        package_weight=Decimal("1000.00"),
        stock_amount=Decimal("450.00"),
    )

    assert isinstance(ingredient.id, uuid.UUID)
    assert ingredient.owner == user
    assert ingredient.price_per_gram == Decimal("0.12")
    assert ingredient.calories == Decimal("0.00")
    assert ingredient.proteins == Decimal("0.00")


@pytest.mark.django_db
def test_ingredient_db_constraints_prevent_invalid_values():
    """Проверяем, что ограничения БД запрещают отрицательную цену и нулевой вес упаковки."""
    user = User.objects.create_user(email="chef@foodcalc.local", password="Password123!")

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.create(
            owner=user,
            name="Ошибочный продукт 1",
            purchase_price=Decimal("-10.00"),
            package_weight=Decimal("500.00"),
        )

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.create(
            owner=user,
            name="Ошибочный продукт 2",
            purchase_price=Decimal("100.00"),
            package_weight=Decimal("0.00"),
        )


@pytest.mark.django_db
def test_recipe_calculations_and_snapshot_immutability():
    """
    Проверяем авторасчет рецепта (вес, себестоимость, запас, КБЖУ)
    и неизменяемость snapshot при последующем скачке цен в каталоге.
    """
    user = User.objects.create_user(email="pastry@foodcalc.local", password="Password123!")

    butter = Ingredient.objects.create(
        owner=user,
        name="Сливочное масло 82.5%",
        purchase_price=Decimal("200.00"),
        package_weight=Decimal("200.00"),  # 1 руб/г
        stock_amount=Decimal("400.00"),
        calories=Decimal("748.00"),
        proteins=Decimal("0.60"),
        fats=Decimal("82.50"),
        carbs=Decimal("0.80"),
    )
    sugar = Ingredient.objects.create(
        owner=user,
        name="Сахарная пудра",
        purchase_price=Decimal("100.00"),
        package_weight=Decimal("500.00"),  # 0.20 руб/г
        stock_amount=Decimal("500.00"),
        calories=Decimal("398.00"),
        proteins=Decimal("0.00"),
        fats=Decimal("0.00"),
        carbs=Decimal("99.80"),
    )

    recipe = Recipe.objects.create(
        owner=user,
        name="Базовый крем",
        instructions="Взбить масло с сахарной пудрой до пышности.",
        is_semi_finished=True,
        safety_margin_percent=Decimal("10.00"),
    )

    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=butter,
        amount_grams=Decimal("100.00"),  # 100 руб
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=sugar,
        amount_grams=Decimal("100.00"),  # 20 руб
    )

    # Итого вес: 200 г, базовая стоимость: 120.00 руб, с запасом +10%: 132.00 руб
    assert recipe.calculated_weight == Decimal("200.00")
    assert recipe.total_weight == Decimal("200.00")
    assert recipe.base_cost == Decimal("120.00")
    assert recipe.planned_cost == Decimal("132.00")

    # Итого калорий: 748 + 398 = 1146 ккал (на 200 г) -> 573 ккал на 100 г
    assert recipe.total_calories == Decimal("1146.00")
    assert recipe.calories_per_100g == Decimal("573.00")

    # Формируем snapshot для заказа и валидируем через схему
    snapshot_dict = recipe.to_snapshot()
    validated_snapshot = RecipeSnapshotSchema.model_validate(snapshot_dict)
    assert validated_snapshot.planned_cost == Decimal("132.00")
    assert len(validated_snapshot.items) == 2

    # Меняем цену масла в каталоге в 2 раза (с 200 до 400 руб)
    butter.purchase_price = Decimal("400.00")
    butter.save()

    # В каталоге рецепт пересчитался, а сохраненный snapshot заказа остался неизменным
    assert recipe.base_cost == Decimal("220.00")
    assert validated_snapshot.base_cost == Decimal("120.00")
    assert validated_snapshot.planned_cost == Decimal("132.00")


@pytest.mark.django_db
def test_duplicate_ingredient_in_recipe_raises_error():
    """Проверяем запрет на дублирование одного ингредиента в рецепте на уровне БД и схемы."""
    user = User.objects.get_system_user()
    ing = Ingredient.objects.create(
        owner=user,
        name="Соль",
        purchase_price=Decimal("50.00"),
        package_weight=Decimal("1000.00"),
    )
    recipe = Recipe.objects.create(owner=user, name="Тесто")
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing,
        amount_grams=Decimal("10.00"),
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ing,
            amount_grams=Decimal("5.00"),
        )

    with pytest.raises(ValidationError):
        RecipeCreateSchema(
            name="Тесто с дублем",
            items=[
                {"ingredient_id": ing.id, "amount_grams": Decimal("10.00")},
                {"ingredient_id": ing.id, "amount_grams": Decimal("5.00")},
            ],
        )


@pytest.mark.django_db
def test_pydantic_schemas_serialization_and_validation():
    """Проверяем сериализацию ORM-моделей через Out-схемы и валидацию входных данных."""
    user = User.objects.create_user(email="schema@foodcalc.local", password="Password123!")

    create_data = IngredientCreateSchema(
        name="  Миндальная мука  ",
        purchase_price=Decimal("650.00"),
        package_weight=Decimal("500.00"),
        stock_amount=Decimal("200.00"),
    )
    assert create_data.name == "Миндальная мука"

    ing = Ingredient.objects.create(owner=user, **create_data.model_dump())
    ing_out = IngredientOutSchema.from_orm(ing)
    assert ing_out.price_per_gram == Decimal("1.30")

    recipe = Recipe.objects.create(owner=user, name="Макарон")
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing,
        amount_grams=Decimal("100.00"),
    )

    recipe_out = RecipeOutSchema.from_orm(recipe)
    assert recipe_out.base_cost == Decimal("130.00")
    assert len(recipe_out.items) == 1
    assert recipe_out.items[0].ingredient_name == "Миндальная мука"

    with pytest.raises(ValidationError):
        IngredientCreateSchema(
            name="   ",
            purchase_price=Decimal("100.00"),
            package_weight=Decimal("100.00"),
        )