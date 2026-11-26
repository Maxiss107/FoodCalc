from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Status
from ninja_jwt.authentication import JWTAuth

from apps.accounts.schemas import ErrorSchema
from apps.orders.models import Order
from apps.orders.schemas import (
    OrderCreateSchema,
    OrderOut,
    OrderStatusUpdateSchema,
    PlanFactInSchema,
    PlanFactOutSchema,
)
from apps.orders.services import (
    create_order,
    get_order,
    list_orders,
    save_order_plan_fact,
    update_order_status,
)

router = Router(tags=["Orders"], auth=JWTAuth())


@router.get("", response={200: list[OrderOut]})
def get_orders(request: HttpRequest, status: Order.Status | None = None) -> list[OrderOut]:
    return list_orders(user=request.auth, status=status)


@router.post("", response={201: OrderOut, 404: ErrorSchema})
def add_order(request: HttpRequest, payload: OrderCreateSchema) -> Status[OrderOut]:
    order = create_order(user=request.auth, data=payload)
    return Status(201, order)


@router.get("/{order_id}", response={200: OrderOut, 404: ErrorSchema})
def get_order_detail(request: HttpRequest, order_id: UUID) -> OrderOut:
    return get_order(user=request.auth, order_id=order_id)


@router.patch("/{order_id}/status", response={200: OrderOut, 404: ErrorSchema})
def patch_order_status(
    request: HttpRequest,
    order_id: UUID,
    payload: OrderStatusUpdateSchema,
) -> OrderOut:
    return update_order_status(user=request.auth, order_id=order_id, status=payload.status)


@router.post("/{order_id}/plan-fact", response={200: PlanFactOutSchema, 404: ErrorSchema})
def post_order_plan_fact(
    request: HttpRequest,
    order_id: UUID,
    payload: PlanFactInSchema,
) -> PlanFactOutSchema:
    return save_order_plan_fact(user=request.auth, order_id=order_id, data=payload)
