from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.catalog.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient
from apps.recipes.schemas import RecipeCreateSchema, RecipeUpdateSchema


def list_recipes(
    user: User,
    is_semi_finished: bool | None = None,
    search: str | None = None,
) -> QuerySet[Recipe]:
    """
    Возвращает список технологических карт, доступных пользователю:
    - личные рецепты пользователя;
    - встроенные системные шаблоны.

    Поддерживает фильтрацию по типу (полуфабрикаты/блюда) и поиск по названию.
    """
    qs = Recipe.objects.filter(Q(owner=user) | Q(owner__is_system=True)).prefetch_related(
        "recipe_ingredients__ingredient"
    )

    if is_semi_finished is not None:
        qs = qs.filter(is_semi_finished=is_semi_finished)

    if search:
        cleaned_search = search.strip()
        if cleaned_search:
            qs = qs.filter(name__icontains=cleaned_search)

    return qs.order_by("-created_at")


def get_recipe(user: User, recipe_id: UUID) -> Recipe:
    """
    Возвращает карточку рецепта с составом ингредиентов, если он принадлежит
    пользователю или является системным шаблоном.
    """
    recipe = (
        Recipe.objects.filter(Q(id=recipe_id) & (Q(owner=user) | Q(owner__is_system=True)))
        .prefetch_related("recipe_ingredients__ingredient")
        .first()
    )
    if not recipe:
        raise HttpError(404, "Рецепт не найден.")
    return recipe


@transaction.atomic
def create_recipe(user: User, data: RecipeCreateSchema) -> Recipe:
    """
    Создает новый рецепт или полуфабрикат с привязанным составом ингредиентов.
    Проверяет доступность всех входящих ингредиентов для пользователя.
    """
    item_ingredient_ids = [item.ingredient_id for item in data.items]
    if item_ingredient_ids:
        accessible_count = (
            Ingredient.objects.filter(id__in=item_ingredient_ids)
            .filter(Q(owner=user) | Q(owner__is_system=True))
            .count()
        )
        if accessible_count != len(item_ingredient_ids):
            raise HttpError(
                400,
                "Один или несколько выбранных ингредиентов не найдены или недоступны.",
            )

    recipe = Recipe.objects.create(
        owner=user,
        name=data.name,
        instructions=data.instructions,
        is_semi_finished=data.is_semi_finished,
        output_weight=data.output_weight,
        safety_margin_percent=data.safety_margin_percent,
    )

    for item in data.items:
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient_id=item.ingredient_id,
            amount_grams=item.amount_grams,
        )

    return get_recipe(user=user, recipe_id=recipe.id)


@transaction.atomic
def update_recipe(user: User, recipe_id: UUID, data: RecipeUpdateSchema) -> Recipe:
    """
    Обновляет рецепт и его состав (только для личных рецептов пользователя).
    При передаче нового состава `items` текущие позиции заменяются на новые.
    """
    recipe = Recipe.objects.filter(id=recipe_id).first()
    if not recipe:
        raise HttpError(404, "Рецепт не найден.")

    if recipe.owner_id != user.id:
        if getattr(recipe.owner, "is_system", False):
            raise HttpError(403, "Запрещено редактировать системный шаблон рецепта.")
        raise HttpError(404, "Рецепт не найден.")

    dumped = data.model_dump(exclude_unset=True)
    items_data = dumped.pop("items", None)

    for field, value in dumped.items():
        if value is not None:
            setattr(recipe, field, value)

    recipe.save()

    if items_data is not None:
        item_ingredient_ids = [item["ingredient_id"] for item in items_data]
        if item_ingredient_ids:
            accessible_count = (
                Ingredient.objects.filter(id__in=item_ingredient_ids)
                .filter(Q(owner=user) | Q(owner__is_system=True))
                .count()
            )
            if accessible_count != len(item_ingredient_ids):
                raise HttpError(
                    400,
                    "Один или несколько выбранных ингредиентов не найдены или недоступны.",
                )

        recipe.recipe_ingredients.all().delete()
        for item in items_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=item["ingredient_id"],
                amount_grams=item["amount_grams"],
            )

    return get_recipe(user=user, recipe_id=recipe.id)


def delete_recipe(user: User, recipe_id: UUID) -> None:
    """Удаляет рецепт пользователя. Системные шаблоны удалять запрещено."""
    recipe = Recipe.objects.filter(id=recipe_id).first()
    if not recipe:
        raise HttpError(404, "Рецепт не найден.")

    if recipe.owner_id != user.id:
        if getattr(recipe.owner, "is_system", False):
            raise HttpError(403, "Запрещено удалять системный шаблон рецепта.")
        raise HttpError(404, "Рецепт не найден.")

    recipe.delete()


def get_recipe_snapshot(user: User, recipe_id: UUID) -> dict:
    """
    Возвращает неизменяемый снимок (snapshot) рецепта со всеми расчетами
    для интеграции с карточками заказов (apps/orders).
    """
    recipe = get_recipe(user=user, recipe_id=recipe_id)
    return recipe.to_snapshot()


@transaction.atomic
def copy_template_recipe(user: User, recipe_id: UUID) -> Recipe:
    """
    Копирует системный шаблон рецепта в личную книгу рецептов пользователя.
    """
    template = Recipe.objects.filter(id=recipe_id).prefetch_related("recipe_ingredients").first()
    if not template or not getattr(template.owner, "is_system", False):
        raise HttpError(404, "Системный шаблон рецепта не найден.")

    new_recipe = Recipe.objects.create(
        owner=user,
        name=f"{template.name} (копия)",
        instructions=template.instructions,
        is_semi_finished=template.is_semi_finished,
        output_weight=template.output_weight,
        safety_margin_percent=template.safety_margin_percent,
    )

    for item in template.recipe_ingredients.all():
        RecipeIngredient.objects.create(
            recipe=new_recipe,
            ingredient_id=item.ingredient_id,
            amount_grams=item.amount_grams,
        )

    return get_recipe(user=user, recipe_id=new_recipe.id)
