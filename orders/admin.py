from django.contrib import admin
from .models import Order, OrderItem
from .models import OrderStatusHistory

admin.site.register(Order)
admin.site.register(OrderItem)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'previous_status', 'new_status', 'changed_at')
    list_filter = ('previous_status', 'new_status', 'changed_at')
