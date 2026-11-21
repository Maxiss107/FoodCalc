from ninja import NinjaAPI

from apps.accounts.router import router

api = NinjaAPI(
    title="FoodCalc API",
    version="1.0.0",
    description="API for calculating food cost, macronutrient content, and order management",
)

api.add_router("/auth", router)
