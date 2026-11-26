from uuid import UUID

from ninja import Router
from ninja_jwt.authentication import JWTAuth

from apps.orders.schemas import ShoppingCalcRequestSchema, ShoppingListOut
from apps.orders.services import calculate_order_shopping_list

router = Router(tags=["Orders & Shopping"], auth=JWTAuth())


@router.post(
    "/{order_id}/shopping-list",
    response=ShoppingListOut,
    summary="Calculate the shopping list for a user's order",
)
def get_order_shopping_list(
    request,
    order_id: UUID,
    payload: ShoppingCalcRequestSchema | None = None,
):
    """POST-эндпоинт расчёта таблицы закупок для заказа с опциональными ручными правками веса и цены."""
    return calculate_order_shopping_list(
        user=request.auth,
        order_id=order_id,
        data=payload,
    )
