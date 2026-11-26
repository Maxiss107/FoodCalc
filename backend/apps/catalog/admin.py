from django.contrib import admin

from apps.catalog.models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Конфигурация отображения модели Ingredient в панели администратора Django."""

    list_display = (
        "name",
        "owner",
        "purchase_price",
        "package_weight",
        "stock_amount",
        "calories",
        "created_at",
    )
    list_filter = ("owner", "created_at")
    search_fields = ("name", "owner__email")
    readonly_fields = ("id", "price_per_gram", "created_at", "updated_at")
