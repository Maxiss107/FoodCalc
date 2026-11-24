from django.contrib import admin

from apps.recipes.models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    """Встроенное редактирование состава рецепта прямо на странице карточки рецепта."""

    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Конфигурация отображения модели Recipe в панели администратора Django."""

    list_display = (
        "name",
        "owner",
        "is_semi_finished",
        "total_weight",
        "base_cost",
        "planned_cost",
        "created_at",
    )
    list_filter = ("is_semi_finished", "owner", "created_at")
    search_fields = ("name", "owner__email")
    readonly_fields = (
        "id",
        "calculated_weight",
        "total_weight",
        "base_cost",
        "planned_cost",
        "total_calories",
        "total_proteins",
        "total_fats",
        "total_carbs",
        "created_at",
        "updated_at",
    )
    inlines = (RecipeIngredientInline,)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Конфигурация отображения связующей модели RecipeIngredient в админ-панели."""

    list_display = (
        "recipe",
        "ingredient",
        "amount_grams",
        "cost",
        "created_at",
    )
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name")
    readonly_fields = ("id", "cost", "created_at", "updated_at")