from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Ingredient
from core.models import CoreModel, OwnedModel

TWO_PLACES = Decimal("0.01")
HUNDRED = Decimal("100.00")


class Recipe(OwnedModel):
    """
    Модель технологической карты рецепта или переиспользуемого полуфабриката.

    Наследование от OwnedModel обеспечивает:
    - первичный ключ id (UUID v4), метки времени created_at и updated_at;
    - поле owner (ссылка на аккаунт мастера или системного пользователя
      для встроенных шаблонов рецептов).

    Обеспечивает автоматический расчет итогового веса, базовой и плановой
    себестоимости (с учетом процента запаса), пищевой ценности (КБЖУ) на
    весь выход и на 100 грамм, а также генерацию снимка данных (snapshot)
    для фиксации параметров при создании заказа.
    """

    name = models.CharField(
        max_length=255,
        verbose_name="Recipe name",
    )
    instructions = models.TextField(
        blank=True,
        default="",
        verbose_name="Cooking instructions",
    )
    is_semi_finished = models.BooleanField(
        default=False,
        verbose_name="Is semi-finished product",
    )
    output_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Custom output weight (grams)",
    )
    safety_margin_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        verbose_name="Price safety margin (%)",
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ingredients",
    )

    class Meta(OwnedModel.Meta):
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(output_weight__isnull=True)
                    | models.Q(output_weight__gt=Decimal("0.00"))
                ),
                name="recipe_output_weight_gt_0_or_null",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(safety_margin_percent__gte=Decimal("0.00"))
                    & models.Q(safety_margin_percent__lte=HUNDRED)
                ),
                name="recipe_safety_margin_between_0_and_100",
            ),
        )

    def __str__(self) -> str:
        kind = "Semi-finished" if self.is_semi_finished else "Recipe"
        return f"{self.name} ({kind})"

    @property
    def items_list(self) -> list["RecipeIngredient"]:
        """Возвращает список позиций состава рецепта с предзагруженными ингредиентами."""
        return list(self.recipe_ingredients.select_related("ingredient").all())

    @property
    def calculated_weight(self) -> Decimal:
        """Сумма граммовок всех входящих в рецепт ингредиентов."""
        total = sum(
            (item.amount_grams for item in self.items_list),
            start=Decimal("0.00"),
        )
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def total_weight(self) -> Decimal:
        """
        Итоговый вес готового изделия в граммах.
        Если задан ручной вес выхода (output_weight), возвращает его;
        иначе возвращает сумму граммовок ингредиентов (calculated_weight).
        """
        if self.output_weight and self.output_weight > Decimal("0.00"):
            return self.output_weight.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return self.calculated_weight

    @property
    def base_cost(self) -> Decimal:
        """Чистая себестоимость всех ингредиентов рецепта без учета процента запаса."""
        total = sum(
            (item.cost for item in self.items_list),
            start=Decimal("0.00"),
        )
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def planned_cost(self) -> Decimal:
        """
        Плановая себестоимость рецепта с учетом процента запаса (safety_margin_percent)
        для защиты от скачков цен на сырье.
        """
        multiplier = Decimal("1.00") + (self.safety_margin_percent / HUNDRED)
        return (self.base_cost * multiplier).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def total_calories(self) -> Decimal:
        """Суммарная калорийность всего блюда (ккал)."""
        total = sum((item.calories for item in self.items_list), start=Decimal("0.00"))
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def total_proteins(self) -> Decimal:
        """Суммарное количество белков во всем блюде (г)."""
        total = sum((item.proteins for item in self.items_list), start=Decimal("0.00"))
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def total_fats(self) -> Decimal:
        """Суммарное количество жиров во всем блюде (г)."""
        total = sum((item.fats for item in self.items_list), start=Decimal("0.00"))
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def total_carbs(self) -> Decimal:
        """Суммарное количество углеводов во всем блюде (г)."""
        total = sum((item.carbs for item in self.items_list), start=Decimal("0.00"))
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def calories_per_100g(self) -> Decimal:
        """Калорийность на 100 грамм готового продукта (ккал)."""
        weight = self.total_weight
        if weight <= Decimal("0.00"):
            return Decimal("0.00")
        return ((self.total_calories / weight) * HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @property
    def proteins_per_100g(self) -> Decimal:
        """Белки на 100 грамм готового продукта (г)."""
        weight = self.total_weight
        if weight <= Decimal("0.00"):
            return Decimal("0.00")
        return ((self.total_proteins / weight) * HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @property
    def fats_per_100g(self) -> Decimal:
        """Жиры на 100 грамм готового продукта (г)."""
        weight = self.total_weight
        if weight <= Decimal("0.00"):
            return Decimal("0.00")
        return ((self.total_fats / weight) * HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def carbs_per_100g(self) -> Decimal:
        """Углеводы на 100 грамм готового продукта (г)."""
        weight = self.total_weight
        if weight <= Decimal("0.00"):
            return Decimal("0.00")
        return ((self.total_carbs / weight) * HUNDRED).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    def to_snapshot(self) -> dict[str, Any]:
        """
        Формирует неизменяемый снимок (snapshot) рецепта и его состава со всеми
        текущими ценами, граммовками и КБЖУ для сохранения в карточке заказа (OrderItem).
        Гарантирует, что будущие изменения цен или рецептуры в каталоге не исказят
        историю и план-факт созданного заказа.
        """
        return {
            "recipe_id": str(self.id),
            "name": self.name,
            "is_semi_finished": self.is_semi_finished,
            "instructions": self.instructions,
            "total_weight": str(self.total_weight),
            "base_cost": str(self.base_cost),
            "safety_margin_percent": str(self.safety_margin_percent),
            "planned_cost": str(self.planned_cost),
            "nutrition_total": {
                "calories": str(self.total_calories),
                "proteins": str(self.total_proteins),
                "fats": str(self.total_fats),
                "carbs": str(self.total_carbs),
            },
            "nutrition_per_100g": {
                "calories": str(self.calories_per_100g),
                "proteins": str(self.proteins_per_100g),
                "fats": str(self.fats_per_100g),
                "carbs": str(self.carbs_per_100g),
            },
            "items": [
                {
                    "ingredient_id": str(item.ingredient_id),
                    "ingredient_name": item.ingredient.name,
                    "amount_grams": str(item.amount_grams),
                    "purchase_price": str(item.ingredient.purchase_price),
                    "package_weight": str(item.ingredient.package_weight),
                    "item_cost": str(item.cost),
                }
                for item in self.items_list
            ],
        }


class RecipeIngredient(CoreModel):
    """
    Связующая модель состава рецепта (промежуточная таблица Recipe <-> Ingredient).

    Наследуется от CoreModel (UUID id, created_at, updated_at).
    Хранит точную граммовку (amount_grams) конкретного ингредиента в рецепте
    и предоставляет расчетные свойства стоимости и макронутриентов этой позиции.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Recipe",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_usages",
        verbose_name="Ingredient",
    )
    amount_grams = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Amount in recipe (grams)",
    )

    class Meta(CoreModel.Meta):
        verbose_name = "Recipe ingredient"
        verbose_name_plural = "Recipe ingredients"
        constraints = (
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
            models.CheckConstraint(
                condition=models.Q(amount_grams__gt=Decimal("0.00")),
                name="recipe_ingredient_amount_grams_gt_0",
            ),
        )

    def __str__(self) -> str:
        return f"{self.ingredient.name} — {self.amount_grams}g in {self.recipe.name}"

    @property
    def cost(self) -> Decimal:
        """Расчетная стоимость данного объема ингредиента в рецепте."""
        raw_cost = self.ingredient.price_per_gram * self.amount_grams
        return raw_cost.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def calories(self) -> Decimal:
        """Калорийность данной граммовки ингредиента (ккал)."""
        return ((self.ingredient.calories * self.amount_grams) / HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @property
    def proteins(self) -> Decimal:
        """Белки в данной граммовке ингредиента (г)."""
        return ((self.ingredient.proteins * self.amount_grams) / HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @property
    def fats(self) -> Decimal:
        """Жиры в данной граммовке ингредиента (г)."""
        return ((self.ingredient.fats * self.amount_grams) / HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @property
    def carbs(self) -> Decimal:
        """Углеводы в данной граммовке ингредиента (г)."""
        return ((self.ingredient.carbs * self.amount_grams) / HUNDRED).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
