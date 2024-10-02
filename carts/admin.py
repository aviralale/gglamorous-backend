from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # Number of empty inline forms to display
    fields = ['product', 'size', 'quantity']  # Fields to display in inline form


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']  # Display user and created_at in the cart list
    inlines = [CartItemInline]  # Show related CartItems inline within the Cart view
    search_fields = ['user__username']  # Allow search by user's username
    list_filter = ['created_at']  # Filter by creation date

    def get_queryset(self, request):
        """
        Override to use 'select_related' and 'prefetch_related' to optimize queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__product')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'size', 'quantity']  # Display cart, product, size, and quantity in the list view
    search_fields = ['cart__user__username', 'product__name']  # Allow search by cart's user or product name
    list_filter = ['cart__user', 'product']  # Filter by cart's user and product
