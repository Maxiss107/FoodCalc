from ninja import NinjaAPI

from apps.accounts.router import router as auth_router
from apps.catalog.router import router as catalog_router
from apps.orders.router import router as orders_router
from apps.recipes.router import router as recipes_router

api = NinjaAPI(
    title="FoodCalc API",
    version="1.0.0",
    description="API for calculating food cost, macronutrient content, and order management",
)

api.add_router("/auth", auth_router)
api.add_router("/catalog", catalog_router)
api.add_router("/recipes", recipes_router)
api.add_router("/orders", orders_router)
