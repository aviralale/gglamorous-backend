from rest_framework import serializers
from .models import Category, Product, ProductImage, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)  # Include related images

    class Meta:
        model = Product
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.first_name')  # Display email instead of username

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'quality_rating', 'value_rating', 'size', 'comment', 'image', 'created_at']
        read_only_fields = ['user', 'created_at']

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