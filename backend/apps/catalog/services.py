from decimal import Decimal
from uuid import UUID

from django.db.models import Q, QuerySet
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.catalog.models import Ingredient
from apps.catalog.schemas import IngredientCreateSchema, IngredientUpdateSchema


def list_ingredients(user: User, search: str | None = None) -> QuerySet[Ingredient]:
    """
    Возвращает список ингредиентов, доступных пользователю:
    - личные ингредиенты пользователя (owner=user);
    - встроенные системные шаблоны (owner__is_system=True).

    Поддерживает поиск по подстроке в названии (регистронезависимо).
    """
    qs = Ingredient.objects.filter(Q(owner=user) | Q(owner__is_system=True))
    if search:
        cleaned_search = search.strip()
        if cleaned_search:
            qs = qs.filter(name__icontains=cleaned_search)
    return qs.order_by("-created_at")


def get_ingredient(user: User, ingredient_id: UUID) -> Ingredient:
    """
    Возвращает ингредиент по его ID, если он принадлежит пользователю
    или является системным шаблоном.
    """
    ingredient = Ingredient.objects.filter(
        Q(id=ingredient_id) & (Q(owner=user) | Q(owner__is_system=True))
    ).first()
    if not ingredient:
        raise HttpError(404, "Ингредиент не найден.")
    return ingredient


def create_ingredient(user: User, data: IngredientCreateSchema) -> Ingredient:
    """Создает новый ингредиент в личном каталоге пользователя."""
    return Ingredient.objects.create(
        owner=user,
        **data.model_dump(),
    )


def update_ingredient(user: User, ingredient_id: UUID, data: IngredientUpdateSchema) -> Ingredient:
    """
    Обновляет данные ингредиента (только для личных ингредиентов пользователя).
    Попытка изменить системный шаблон возвращает 403 Forbidden.
    """
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        raise HttpError(404, "Ингредиент не найден.")

    if ingredient.owner_id != user.id:
        if getattr(ingredient.owner, "is_system", False):
            raise HttpError(403, "Запрещено редактировать системный шаблон.")
        raise HttpError(404, "Ингредиент не найден.")

    update_fields: list[str] = []
    dumped = data.model_dump(exclude_unset=True)
    for field, value in dumped.items():
        if value is not None:
            setattr(ingredient, field, value)
            update_fields.append(field)

    if update_fields:
        ingredient.save(update_fields=update_fields)

    return ingredient


def delete_ingredient(user: User, ingredient_id: UUID) -> None:
    """
    Удаляет ингредиент из личного каталога пользователя.
    Системные шаблоны удалять запрещено.
    """
    ingredient = Ingredient.objects.filter(id=ingredient_id).first()
    if not ingredient:
        raise HttpError(404, "Ингредиент не найден.")

    if ingredient.owner_id != user.id:
        if getattr(ingredient.owner, "is_system", False):
            raise HttpError(403, "Запрещено удалять системный шаблон.")
        raise HttpError(404, "Ингредиент не найден.")

    ingredient.delete()


def copy_template_ingredient(
    user: User, ingredient_id: UUID, stock_amount: Decimal | None = None
) -> Ingredient:
    """
    Копирует системный шаблон ингредиента на личный склад пользователя.
    """
    template = Ingredient.objects.filter(id=ingredient_id).first()
    if not template or not getattr(template.owner, "is_system", False):
        raise HttpError(404, "Системный шаблон ингредиента не найден.")

    stock = stock_amount if stock_amount is not None else Decimal("0.00")
    return Ingredient.objects.create(
        owner=user,
        name=template.name,
        purchase_price=template.purchase_price,
        package_weight=template.package_weight,
        stock_amount=stock,
        calories=template.calories,
        proteins=template.proteins,
        fats=template.fats,
        carbs=template.carbs,
    )
