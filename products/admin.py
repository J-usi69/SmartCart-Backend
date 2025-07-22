from django.contrib import admin
from django.utils.html import format_html
from .models import Product


class LowStockFilter(admin.SimpleListFilter):
    title = 'Stock bajo'
    parameter_name = 'low_stock'

    def lookups(self, request, model_admin):
        return [('yes', 'Sí')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(stock__lt=5)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'highlight_stock', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active', 'created_at', LowStockFilter)
    ordering = ('-created_at',)


    filter_horizontal = ('related_products',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price', 'stock', 'is_active')
        }),
        ('Descuentos', {
            'fields': ('has_discount', 'discount_percentage')
        }),
        ('Recomendaciones', {
            'fields': ('related_products',),
            'description': 'Selecciona productos para recomendar junto con este producto',
            'classes': ('collapse',)  # Hacer que esta sección sea colapsable
        })
    )

    def highlight_stock(self, obj):
        if obj.stock < 6:
            color = 'red'
        else:
            color = 'black'
        return format_html('<span style="color: {};">{}</span>', color, obj.stock)

    highlight_stock.short_description = 'Stock'
