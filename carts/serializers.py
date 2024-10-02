from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'size', 'quantity', 'cart']

    def validate_size(self, value):
        """
        Custom validation to ensure the selected size is available for the product.
        """
        product = self.initial_data.get('product')
        if product:
            product_instance = Product.objects.get(pk=product)
            available_sizes = product_instance.sizes.keys()
            if value not in available_sizes:
                raise serializers.ValidationError(f"Size '{value}' is not available for this product.")
        return value
    
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'
