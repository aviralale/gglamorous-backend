from rest_framework import serializers
from .models import Wishlist, WishlistItem
from products.models import Product
from products.serializers import ProductSerializer  # Import your existing Product serializer

class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # Nested serializer to display product details

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'size']  # Include size in the fields

class WishlistSerializer(serializers.ModelSerializer):
    wishlist_items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'wishlist_items', 'created_at']
        read_only_fields = ['user']

class WishlistCreateItemSerializer(serializers.ModelSerializer):
    """Serializer for adding a product to a wishlist with size."""
    product_id = serializers.IntegerField()  # Accept product ID as input
    size = serializers.CharField(max_length=10)

    class Meta:
        model = WishlistItem
        fields = ['product_id', 'size']

    def create(self, validated_data):
        """Custom create method to handle wishlist item creation."""
        wishlist = validated_data.get('wishlist')
        product_id = validated_data.get('product_id')
        size = validated_data.get('size')

        # Check if the product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Invalid product ID"})

        # Create or update the WishlistItem with the provided size
        wishlist_item, created = WishlistItem.objects.update_or_create(
            wishlist=wishlist,
            product=product,
            defaults={'size': size}
        )

        return wishlist_item
