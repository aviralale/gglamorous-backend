from django.contrib import admin
from django.db import transaction
from .models import Order, OrderItem
from products.models import Product

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity']
    raw_id_fields = ('product',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields['product'].queryset = Product.objects.all()
        return formset

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'payment_method', 'payment_status', 'status', 'created_at']
    list_filter = ['payment_status', 'status', 'created_at', 'payment_method']
    search_fields = ['user__username', 'transaction_id', 'address__city']
    inlines = [OrderItemInline]
    readonly_fields = ['total_amount', 'transaction_id', 'created_at']
    fieldsets = (
        (None, {'fields': ('user', 'address', 'total_amount', 'payment_method', 'payment_status', 'transaction_id', 'status')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'address').prefetch_related('items__product')

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If this is a new order
            obj.total_amount = 0  # Set a default value
        super().save_model(request, obj, form, change)

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        # Delete objects marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
        
        # Save new and modified instances
        for instance in instances:
            instance.save()
        
        formset.save_m2m()
        
        # Recalculate total_amount after saving inline items
        obj = form.instance
        obj.total_amount = sum(item.quantity * item.product.price for item in obj.items.all())
        obj.save()

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'get_price']
    search_fields = ['order__user__username', 'product__name']
    list_filter = ['order__status', 'product']
    readonly_fields = ['get_price']

    def get_price(self, obj):
        return obj.product.price
    get_price.short_description = 'Price'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order', 'product')