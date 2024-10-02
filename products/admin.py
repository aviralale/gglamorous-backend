from django.contrib import admin
from .models import Category, Product, ProductImage, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of empty forms to display for additional images
    fields = ['image', 'alt_text']  # Fields to show in the inline form
    readonly_fields = []  # Add fields here if you want them to be readonly


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    search_fields = ['name']
    prepopulated_fields = {"slug": ("name",)}  # Automatically generate slug based on name


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_sale', 'created_at', 'updated_at']
    list_filter = ['category', 'is_sale', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {"slug": ("name",)}  # Automatically generate slug based on name
    inlines = [ProductImageInline]  # Show ProductImage model as inline within Product view

    def get_queryset(self, request):
        """
        Override to use 'select_related' to optimize queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('images')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'quality_rating', 'value_rating', 'size', 'created_at']
    list_filter = ['quality_rating', 'value_rating', 'created_at']
    search_fields = ['product__name', 'comment']
    readonly_fields = ['created_at']  # Make created_at read-only
    autocomplete_fields = ['product', 'user']  # Use autocomplete for foreign key fields to optimize query loading

    def get_queryset(self, request):
        """
        Override to use 'select_related' to optimize queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related('product', 'user')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'alt_text']
    search_fields = ['product__name', 'alt_text']
    autocomplete_fields = ['product']  # Use autocomplete for product field to optimize query loading

    def get_queryset(self, request):
        """
        Override to use 'select_related' to optimize queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related('product')
