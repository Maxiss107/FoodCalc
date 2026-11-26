from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem
from apps.orders.schemas import OrderCreateSchema, PlanFactInSchema, PlanFactOutSchema
from apps.recipes.models import Recipe

TWO_PLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def list_orders(user: User, status: Order.Status | None = None) -> QuerySet[Order]:
    qs = Order.objects.filter(owner=user).prefetch_related("items")
    if status is not None:
        qs = qs.filter(status=status)
    return qs


def get_order(user: User, order_id: UUID) -> Order:
    order = Order.objects.filter(id=order_id, owner=user).prefetch_related("items").first()
    if not order:
        raise HttpError(404, "Заказ не найден.")
    return order


@transaction.atomic
def create_order(user: User, data: OrderCreateSchema) -> Order:
    order = Order.objects.create(
        owner=user,
        customer_name=data.customer_name,
        total_price=data.total_price,
    )

    for item in data.items:
        recipe = Recipe.objects.filter(
            Q(id=item.recipe_id) & (Q(owner=user) | Q(owner__is_system=True))
        ).first()
        if not recipe:
            raise HttpError(404, "Рецепт не найден.")

        OrderItem.objects.create(
            order=order,
            recipe=recipe,
            recipe_title_snapshot=recipe.name,
            unit_cost_snapshot=recipe.planned_cost,
            recipe_snapshot=recipe.to_snapshot(),
        )

    return get_order(user, order.id)


def update_order_status(user: User, order_id: UUID, status: Order.Status) -> Order:
    order = get_order(user, order_id)
    order.status = status
    order.save(update_fields=["status", "updated_at"])
    return order


def calculate_plan_fact(
    order_price: Decimal,
    planned_cost: Decimal,
    actual_cost: Decimal,
    actual_time_minutes: int,
) -> dict[str, Decimal | None]:
    actual_profit = _money(order_price - actual_cost)
    hourly_rate = None
    if actual_time_minutes > 0:
        hours = Decimal(actual_time_minutes) / Decimal("60")
        hourly_rate = _money(actual_profit / hours)

    return {
        "cost_deviation": _money(actual_cost - planned_cost),
        "planned_profit": _money(order_price - planned_cost),
        "actual_profit": actual_profit,
        "hourly_rate": hourly_rate,
    }


def save_order_plan_fact(user: User, order_id: UUID, data: PlanFactInSchema) -> PlanFactOutSchema:
    order = get_order(user, order_id)
    order.actual_cost = data.actual_cost
    order.actual_time_minutes = data.actual_time_minutes
    order.save(update_fields=["actual_cost", "actual_time_minutes", "updated_at"])

    planned_cost = order.planned_cost
    values = calculate_plan_fact(
        order_price=order.total_price,
        planned_cost=planned_cost,
        actual_cost=data.actual_cost,
        actual_time_minutes=data.actual_time_minutes,
    )

    return PlanFactOutSchema(
        order_id=order.id,
        order_price=order.total_price,
        planned_cost=planned_cost,
        actual_cost=data.actual_cost,
        actual_time_minutes=data.actual_time_minutes,
        cost_deviation=values["cost_deviation"],
        planned_profit=values["planned_profit"],
        actual_profit=values["actual_profit"],
        hourly_rate=values["hourly_rate"],
    )
