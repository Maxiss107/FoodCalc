from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Status
from ninja_jwt.authentication import JWTAuth

from apps.accounts.schemas import ErrorSchema
from apps.recipes.schemas import (
    RecipeCreateSchema,
    RecipeOutSchema,
    RecipeSnapshotSchema,
    RecipeUpdateSchema,
)
from apps.recipes.services import (
    copy_template_recipe,
    create_recipe,
    delete_recipe,
    get_recipe,
    get_recipe_snapshot,
    list_recipes,
    update_recipe,
)

router = Router(tags=["Recipes"], auth=JWTAuth())


@router.get(
    "",
    response={200: list[RecipeOutSchema]},
    summary="Получить список рецептов и полуфабрикатов",
)
def get_recipes(
    request: HttpRequest,
    is_semi_finished: bool | None = None,
    q: str | None = None,
) -> list[RecipeOutSchema]:
    """Возвращает список рецептов пользователя и шаблонов с фильтрацией по типу и поиском."""
    return list_recipes(user=request.auth, is_semi_finished=is_semi_finished, search=q)


@router.post(
    "",
    response={201: RecipeOutSchema, 400: ErrorSchema},
    summary="Создать новую технологическую карту (рецепт / полуфабрикат)",
)
def add_recipe(
    request: HttpRequest,
    payload: RecipeCreateSchema,
) -> Status[RecipeOutSchema]:
    """Создает рецепт с составом ингредиентов и автоматически рассчитывает себестоимость и КБЖУ."""
    recipe = create_recipe(user=request.auth, data=payload)
    return Status(201, recipe)


@router.get(
    "/{recipe_id}",
    response={200: RecipeOutSchema, 404: ErrorSchema},
    summary="Получить технологическую карту рецепта по ID",
)
def get_recipe_detail(
    request: HttpRequest,
    recipe_id: UUID,
) -> RecipeOutSchema:
    """Возвращает полную карточку рецепта со всеми расчетами и составом."""
    return get_recipe(user=request.auth, recipe_id=recipe_id)


@router.patch(
    "/{recipe_id}",
    response={200: RecipeOutSchema, 400: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema},
    summary="Обновить технологическую карту рецепта или его состав",
)
def patch_recipe(
    request: HttpRequest,
    recipe_id: UUID,
    payload: RecipeUpdateSchema,
) -> RecipeOutSchema:
    """Обновляет параметры рецепта и/или заменяет список ингредиентов."""
    return update_recipe(user=request.auth, recipe_id=recipe_id, data=payload)


@router.delete(
    "/{recipe_id}",
    response={204: None, 403: ErrorSchema, 404: ErrorSchema},
    summary="Удалить технологическую карту",
)
def remove_recipe(
    request: HttpRequest,
    recipe_id: UUID,
) -> Status[None]:
    """Удаляет рецепт пользователя из базы."""
    delete_recipe(user=request.auth, recipe_id=recipe_id)
    return Status(204, None)


@router.get(
    "/{recipe_id}/snapshot",
    response={200: RecipeSnapshotSchema, 404: ErrorSchema},
    summary="Получить неизменяемый snapshot рецепта для заказа (apps/orders)",
)
def get_snapshot(
    request: HttpRequest,
    recipe_id: UUID,
) -> RecipeSnapshotSchema:
    """Формирует неизменяемый снимок цен, граммовок и КБЖУ для фиксации в OrderItem."""
    return get_recipe_snapshot(user=request.auth, recipe_id=recipe_id)


@router.post(
    "/{recipe_id}/copy",
    response={201: RecipeOutSchema, 404: ErrorSchema},
    summary="Скопировать системный шаблон рецепта в личные рецепты",
)
def copy_recipe(
    request: HttpRequest,
    recipe_id: UUID,
) -> Status[RecipeOutSchema]:
    """Создает копию системного рецепта для пользователя с сохранением состава."""
    copied = copy_template_recipe(user=request.auth, recipe_id=recipe_id)
    return Status(201, copied)
