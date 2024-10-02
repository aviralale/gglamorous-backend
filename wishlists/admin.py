from django.contrib import admin
from .models import Wishlist, WishlistItem

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 1
    readonly_fields = ('product', 'size')


class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_products_with_sizes', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)
    inlines = [WishlistItemInline]  # Add inline to view/edit wishlist items in the same view

    def get_products_with_sizes(self, obj):
        """Display products and their sizes in the wishlist."""
        return ", ".join([f"{item.product.name} ({item.size})" for item in obj.wishlist_items.all()])

    get_products_with_sizes.short_description = 'Products and Sizes'

# Register the Wishlist model with the customized admin view
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(WishlistItem)  # Register WishlistItem for detailed management
