"""
API-роутер технологических карт и рецептов.
Экспортирует router для подключения к NinjaAPI.
"""

from apps.recipes.router import router

__all__ = ["router"]
