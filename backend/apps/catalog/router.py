from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Status
from ninja_jwt.authentication import JWTAuth

from apps.accounts.schemas import ErrorSchema
from apps.catalog.schemas import (
    IngredientCreateSchema,
    IngredientOutSchema,
    IngredientUpdateSchema,
)
from apps.catalog.services import (
    copy_template_ingredient,
    create_ingredient,
    delete_ingredient,
    get_ingredient,
    list_ingredients,
    update_ingredient,
)

router = Router(tags=["Catalog"], auth=JWTAuth())


@router.get(
    "/ingredients",
    response={200: list[IngredientOutSchema]},
    summary="Получить список ингредиентов (личных и системных шаблонов)",
)
def get_ingredients(
    request: HttpRequest,
    q: str | None = None,
) -> list[IngredientOutSchema]:
    """Возвращает список ингредиентов пользователя и шаблонов с опциональной фильтрацией по названию."""
    return list_ingredients(user=request.auth, search=q)


@router.post(
    "/ingredients",
    response={201: IngredientOutSchema, 400: ErrorSchema},
    summary="Добавить новый ингредиент на личный склад",
)
def add_ingredient(
    request: HttpRequest,
    payload: IngredientCreateSchema,
) -> Status[IngredientOutSchema]:
    """Создает новый ингредиент в личном каталоге пользователя."""
    ingredient = create_ingredient(user=request.auth, data=payload)
    return Status(201, ingredient)


@router.get(
    "/ingredients/{ingredient_id}",
    response={200: IngredientOutSchema, 404: ErrorSchema},
    summary="Получить карточку ингредиента по ID",
)
def get_ingredient_detail(
    request: HttpRequest,
    ingredient_id: UUID,
) -> IngredientOutSchema:
    """Возвращает детальную информацию об ингредиенте."""
    return get_ingredient(user=request.auth, ingredient_id=ingredient_id)


@router.patch(
    "/ingredients/{ingredient_id}",
    response={200: IngredientOutSchema, 403: ErrorSchema, 404: ErrorSchema},
    summary="Быстрое обновление цены, остатка или параметров ингредиента",
)
def patch_ingredient(
    request: HttpRequest,
    ingredient_id: UUID,
    payload: IngredientUpdateSchema,
) -> IngredientOutSchema:
    """Частично обновляет карточку личного ингредиента (цена, остаток на кухне, КБЖУ)."""
    return update_ingredient(user=request.auth, ingredient_id=ingredient_id, data=payload)


@router.delete(
    "/ingredients/{ingredient_id}",
    response={204: None, 403: ErrorSchema, 404: ErrorSchema},
    summary="Удалить ингредиент со склада",
)
def remove_ingredient(
    request: HttpRequest,
    ingredient_id: UUID,
) -> Status[None]:
    """Удаляет ингредиент из личного каталога пользователя."""
    delete_ingredient(user=request.auth, ingredient_id=ingredient_id)
    return Status(204, None)


@router.post(
    "/ingredients/{ingredient_id}/copy",
    response={201: IngredientOutSchema, 404: ErrorSchema},
    summary="Скопировать системный шаблон ингредиента на личный склад",
)
def copy_ingredient(
    request: HttpRequest,
    ingredient_id: UUID,
) -> Status[IngredientOutSchema]:
    """Копирует шаблон ингредиента в личный каталог пользователя для дальнейшей кастомизации."""
    copied = copy_template_ingredient(user=request.auth, ingredient_id=ingredient_id)
    return Status(201, copied)
