from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import OwnedModel


class Ingredient(OwnedModel):
    """
    Модель ингредиента (сырья) в каталоге и на личном складе пользователя.

    Наследование от OwnedModel обеспечивает:
    - первичный ключ id (UUID v4), метки времени created_at и updated_at;
    - поле owner (ссылка на пользователя-владельца или системный аккаунт
      для встроенных шаблонов сервиса).

    Хранит параметры фасовки, стоимость закупки, текущий складской остаток
    на кухне и показатели пищевой ценности (КБЖУ) в расчете на 100 грамм.
    """

    name = models.CharField(
        max_length=255,
        verbose_name="Ingredient name",
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Purchase price per package",
    )
    package_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Package weight (grams)",
    )
    stock_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Current kitchen stock (grams)",
    )

    # Пищевая ценность на 100 грамм продукта (по умолчанию 0 для быстрого ввода 4 полей)
    calories = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Calories per 100g (kcal)",
    )
    proteins = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Proteins per 100g (g)",
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Fats per 100g (g)",
    )
    carbs = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Carbohydrates per 100g (g)",
    )

    class Meta(OwnedModel.Meta):
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=Decimal("0.00")),
                name="ingredient_purchase_price_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(package_weight__gt=Decimal("0.00")),
                name="ingredient_package_weight_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(stock_amount__gte=Decimal("0.00")),
                name="ingredient_stock_amount_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(calories__gte=Decimal("0.00")),
                name="ingredient_calories_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(proteins__gte=Decimal("0.00")),
                name="ingredient_proteins_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(fats__gte=Decimal("0.00")),
                name="ingredient_fats_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(carbs__gte=Decimal("0.00")),
                name="ingredient_carbs_gte_0",
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.package_weight}g — {self.purchase_price})"

    @property
    def price_per_gram(self) -> Decimal:
        """
        Расчетная стоимость 1 грамма ингредиента на основе цены и веса пачки.
        Используется при расчете себестоимости рецептов и формировании snapshot.
        """
        if not self.package_weight or self.package_weight <= Decimal("0.00"):
            return Decimal("0.00")
        return self.purchase_price / self.package_weight