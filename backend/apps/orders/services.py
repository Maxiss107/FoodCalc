from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from ninja.errors import HttpError

from apps.accounts.models import User
from apps.catalog.models import Ingredient
from apps.orders.models import Order
from apps.orders.schemas import (
    ShoppingCalcRequestSchema,
    ShoppingListItemOut,
    ShoppingListOut,
    ShoppingOverrideItemSchema,
    ShoppingStatus,
)

TWO_PLACES = Decimal("0.01")

STATUS_LABELS = {
    ShoppingStatus.IN_STOCK: "В наличии",
    ShoppingStatus.PARTIAL: "Докупить",
    ShoppingStatus.OUT_OF_STOCK: "Купить с нуля",
}


def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
    """Преобразует значение в Decimal с округлением до 2 знаков или default при None."""
    raw = default if value is None else value
    return Decimal(str(raw)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _parse_uuid(raw_id: Any) -> UUID | None:
    """Преобразует строковый идентификатор в UUID или возвращает None для пустого значения."""
    return UUID(str(raw_id)) if raw_id else None


def _parse_snapshot_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Нормализует один ингредиент из recipe_snapshot в единый словарь."""
    return {
        "ingredient_id": _parse_uuid(raw.get("ingredient_id")),
        "ingredient_name": (raw.get("ingredient_name") or raw.get("name") or "Без названия"),
        "amount_grams": _to_decimal(raw.get("amount_grams") or raw.get("amount")),
        "package_weight": _to_decimal(raw.get("package_weight"), default="1.00"),
        "purchase_price": _to_decimal(raw.get("purchase_price"), default="0.00"),
    }


def _extract_snapshot_ingredients(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Извлекает и нормализует список ингредиентов из словаря recipe_snapshot."""
    raw_items = snapshot.get("items") or snapshot.get("ingredients") or []
    return [_parse_snapshot_item(raw) for raw in raw_items]


def _aggregate_order_ingredients(
    order: Order,
) -> tuple[dict[str, dict[str, Any]], set[UUID]]:
    """Суммирует требуемые граммовки одинаковых ингредиентов по всем позициям заказа и собирает их UUID."""
    aggregated: dict[str, dict[str, Any]] = {}
    ingredient_ids: set[UUID] = set()

    for order_item in order.items.all():
        snapshot = order_item.recipe_snapshot or {}
        for entry in _extract_snapshot_ingredients(snapshot):
            ing_id = entry["ingredient_id"]
            key = str(ing_id) if ing_id else f"name:{entry['ingredient_name'].lower()}"
            if ing_id:
                ingredient_ids.add(ing_id)

            if key not in aggregated:
                aggregated[key] = {
                    "ingredient_id": ing_id,
                    "ingredient_name": entry["ingredient_name"],
                    "required_grams": Decimal("0.00"),
                    "package_weight": entry["package_weight"],
                    "purchase_price": entry["purchase_price"],
                }
            aggregated[key]["required_grams"] += entry["amount_grams"]

    return aggregated, ingredient_ids


def _resolve_status_and_deficit(
    required_grams: Decimal,
    stock_amount: Decimal,
) -> tuple[ShoppingStatus, Decimal]:
    """Определяет статус закупки (in_stock, partial, out_of_stock) и дефицит в граммах по остатку на складе."""
    if stock_amount >= required_grams:
        return ShoppingStatus.IN_STOCK, Decimal("0.00")
    if stock_amount > Decimal("0.00"):
        deficit = (required_grams - stock_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return ShoppingStatus.PARTIAL, deficit
    return ShoppingStatus.OUT_OF_STOCK, required_grams


def _calculate_packs_and_cost(
    deficit_grams: Decimal,
    package_weight: Decimal,
    purchase_price: Decimal,
) -> tuple[int, Decimal, Decimal]:
    """Рассчитывает число целых пачек с округлением вверх, остаток после покупки и итоговую стоимость дефицита."""
    if deficit_grams <= Decimal("0.00") or package_weight <= Decimal("0.00"):
        return 0, Decimal("0.00"), Decimal("0.00")

    packs_to_buy = int((deficit_grams / package_weight).to_integral_value(rounding=ROUND_CEILING))
    bought_grams = (Decimal(packs_to_buy) * package_weight).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    leftover_grams = (bought_grams - deficit_grams).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    estimated_cost = (Decimal(packs_to_buy) * purchase_price).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    return packs_to_buy, leftover_grams, estimated_cost


def _build_shopping_item(
    entry: dict[str, Any],
    stock_obj: Ingredient | None,
    override: ShoppingOverrideItemSchema | None,
) -> ShoppingListItemOut:
    """Собирает итоговую строку таблицы закупок по ингредиенту с учётом остатка на складе и ручных правок."""
    required_grams = _to_decimal(
        override.required_grams
        if override and override.required_grams is not None
        else entry["required_grams"]
    )
    stock_amount = _to_decimal(stock_obj.stock_amount if stock_obj else Decimal("0.00"))
    package_weight = _to_decimal(
        override.package_weight
        if override and override.package_weight is not None
        else (stock_obj.package_weight if stock_obj else entry["package_weight"]),
        default="1.00",
    )
    purchase_price = _to_decimal(
        override.purchase_price
        if override and override.purchase_price is not None
        else (stock_obj.purchase_price if stock_obj else entry["purchase_price"])
    )

    status, deficit_grams = _resolve_status_and_deficit(required_grams, stock_amount)
    packs_to_buy, leftover_grams, estimated_cost = _calculate_packs_and_cost(
        deficit_grams, package_weight, purchase_price
    )

    return ShoppingListItemOut(
        ingredient_id=entry["ingredient_id"],
        ingredient_name=entry["ingredient_name"],
        required_grams=required_grams,
        stock_amount=stock_amount,
        deficit_grams=deficit_grams,
        status=status,
        status_label=STATUS_LABELS[status],
        package_weight=package_weight,
        purchase_price=purchase_price,
        packs_to_buy=packs_to_buy,
        leftover_grams=leftover_grams,
        estimated_cost=estimated_cost,
    )


def calculate_order_shopping_list(
    user: User,
    order_id: UUID,
    data: ShoppingCalcRequestSchema | None = None,
) -> ShoppingListOut:
    """
    Рассчитывает таблицу закупок под один заказ пользователя с округлением
    дефицита вверх до целых пачек без списания сырья со склада в БД.
    """
    order = Order.objects.filter(id=order_id, owner=user).prefetch_related("items").first()
    if not order:
        raise HttpError(404, "Заказ не найден.")

    overrides_map: dict[UUID, ShoppingOverrideItemSchema] = (
        {item.ingredient_id: item for item in data.overrides} if data and data.overrides else {}
    )

    aggregated, ingredient_ids = _aggregate_order_ingredients(order)

    stock_by_id: dict[UUID, Ingredient] = (
        {ing.id: ing for ing in Ingredient.objects.filter(owner=user, id__in=ingredient_ids)}
        if ingredient_ids
        else {}
    )

    shopping_items = [
        _build_shopping_item(
            entry=entry,
            stock_obj=stock_by_id.get(entry["ingredient_id"]) if entry["ingredient_id"] else None,
            override=overrides_map.get(entry["ingredient_id"]) if entry["ingredient_id"] else None,
        )
        for entry in aggregated.values()
    ]

    total_cost = sum(
        (item.estimated_cost for item in shopping_items),
        Decimal("0.00"),
    ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    return ShoppingListOut(
        order_id=order.id,
        customer_name=order.customer_name,
        items=shopping_items,
        total_estimated_cost=total_cost,
    )
