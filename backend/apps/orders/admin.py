from django.contrib import admin

from apps.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "owner",
        "status",
        "total_price",
        "actual_cost",
        "actual_time_minutes",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "owner__email")
    readonly_fields = ("id", "planned_cost", "created_at", "updated_at")
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "recipe",
        "recipe_title_snapshot",
        "unit_cost_snapshot",
        "created_at",
    )
    search_fields = ("recipe_title_snapshot", "order__customer_name")
    readonly_fields = ("id", "created_at", "updated_at")
