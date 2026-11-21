from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models

from core.models import CoreModel, OwnedModel


class Order(OwnedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PURCHASED = "purchased", "Purchased"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    customer_name = models.CharField(max_length=255, verbose_name="Customer name")
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Total price",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Status",
    )

    class Meta(OwnedModel.Meta):
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self) -> str:
        return self.customer_name


class OrderItem(CoreModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Order",
    )
    # временное поле, пока не добавлена модель recipes.Recipe
    recipe_id = models.UUIDField(null=True, blank=True, verbose_name="Recipe ID")
    recipe_title_snapshot = models.CharField(max_length=255, verbose_name="Recipe title snapshot")
    unit_cost_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Unit cost snapshot",
    )
    recipe_snapshot = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        verbose_name="Recipe snapshot",
    )

    class Meta(CoreModel.Meta):
        verbose_name = "Order item"
        verbose_name_plural = "Order items"

    def __str__(self) -> str:
        return self.recipe_title_snapshot
