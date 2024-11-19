from rest_framework import serializers
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, Product, ProductImage, Review

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']

    def get_product_count(self, obj):
        return obj.products.count()

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 
            'quality_rating', 'value_rating', 'size', 
            'comment', 'image', 'image_url', 'average_rating', 
            'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'product_name']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.first_name or obj.user.email.split('@')[0],
            'email': obj.user.email
        }

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None

    def get_average_rating(self, obj):
        return (obj.quality_rating + obj.value_rating) / 2

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def validate(self, data):
        # Validate ratings range
        if not (1 <= data.get('quality_rating', 5) <= 5):
            raise serializers.ValidationError({
                "quality_rating": "Rating must be between 1 and 5"
            })
        if not (1 <= data.get('value_rating', 5) <= 5):
            raise serializers.ValidationError({
                "value_rating": "Rating must be between 1 and 5"
            })
        return data

    def validate_size(self, value):
        """
        Custom validation to ensure the selected size is available for the product.
        """
        try:
            product_id = self.initial_data.get('product')
            if not product_id:
                raise serializers.ValidationError("Product ID is required")

            product = Product.objects.get(pk=product_id)
            available_sizes = product.sizes.keys()

            if value not in available_sizes:
                raise serializers.ValidationError(
                    f"Size '{value}' is not available. Available sizes are: {', '.join(available_sizes)}"
                )
            return value
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid product ID provided")
        except Exception as e:
            raise serializers.ValidationError(f"Error validating size: {str(e)}")

class ProductBaseSerializer(serializers.ModelSerializer):
    """Base serializer for shared product functionality"""
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    ratings_breakdown = serializers.SerializerMethodField()

    def get_average_rating(self, obj):
        avg_quality = obj.reviews.aggregate(Avg('quality_rating'))['quality_rating__avg'] or 0
        avg_value = obj.reviews.aggregate(Avg('value_rating'))['value_rating__avg'] or 0
        return {
            'overall': round((avg_quality + avg_value) / 2, 1),
            'quality': round(avg_quality, 1),
            'value': round(avg_value, 1)
        }

    def get_ratings_breakdown(self, obj):
        total_reviews = obj.reviews.count()
        if not total_reviews:
            return None

        # Calculate rating distribution (1-5 stars)
        distribution = {}
        for i in range(1, 6):
            quality_count = obj.reviews.filter(quality_rating=i).count()
            value_count = obj.reviews.filter(value_rating=i).count()
            avg_count = (quality_count + value_count) / 2
            distribution[str(i)] = {
                'count': avg_count,
                'percentage': round((avg_count / total_reviews) * 100, 1)
            }

        return {
            'distribution': distribution,
            'total_reviews': total_reviews,
        }

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_available_sizes(self, obj):
        return [
            {
                'size': size,
                'stock': stock,
                'available': stock > 0
            }
            for size, stock in obj.sizes.items()
        ]

    def get_in_stock(self, obj):
        return any(stock > 0 for stock in obj.sizes.values())

    def get_availability_status(self, obj):
        if not obj.available:
            return "unavailable"
        
        total_stock = sum(stock for stock in obj.sizes.values())
        if total_stock == 0:
            return "out_of_stock"
        elif total_stock < 5:
            return "low_stock"
        return "in_stock"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Add discount percentage if sale_price exists
        if representation.get('sale_price'):
            original_price = float(representation['price'])
            sale_price = float(representation['sale_price'])
            discount_percentage = round((1 - sale_price / original_price) * 100)
            representation['discount_percentage'] = discount_percentage

        # Add image URLs
        if representation.get('images') and representation['images']:
            representation['thumbnail'] = representation['images'][0]['image_url']

        # Add availability details
        status = representation['availability_status']
        representation['availability'] = {
            'status': status,
            'message': self.get_availability_message(status),
            'available_sizes': representation['available_sizes']
        }

        # Restructure ratings information
        ratings = representation['average_rating']
        ratings_breakdown = representation['ratings_breakdown']
        representation['ratings'] = {
            'average': ratings,
            'breakdown': ratings_breakdown,
            'total_reviews': representation['review_count']
        }
        
        # Remove redundant fields
        del representation['average_rating']
        del representation['ratings_breakdown']
        del representation['review_count']

        return representation

    def get_availability_message(self, status):
        messages = {
            'in_stock': "Ready to ship",
            'low_stock': "Only a few items left",
            'out_of_stock': "Currently out of stock",
            'unavailable': "This product is not available"
        }
        return messages.get(status, "Status unknown")

class ProductSerializer(ProductBaseSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    sizes = serializers.JSONField(default=dict)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'is_sale', 'is_new', 'sale_price', 'category', 'images', 
            'average_rating', 'ratings_breakdown', 'review_count', 
            'available_sizes', 'in_stock', 'availability_status', 
            'created_at', 'updated_at', 'sizes', 'stock',
            'category_id'
        ]

    def create(self, validated_data):
        # Get sizes data, defaulting to empty dict if not provided
        sizes = validated_data.pop('sizes', {})
        
        # Create the product first
        product = Product.objects.create(**validated_data)
        
        # Handle images if they exist in the context
        request = self.context.get('request')
        if request and request.FILES:
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )
        
        # Update stock based on sizes
        product.stock = sum(sizes.values())
        product.sizes = sizes
        product.save()
        
        return product

    def validate(self, data):
        # Validate if is_sale is True, sale_price must be provided
        if data.get('is_sale', False):
            if not data.get('sale_price'):
                raise serializers.ValidationError({
                    "sale_price": "Sale price is required when product is on sale"
                })
            if float(data['sale_price']) >= float(data['price']):
                raise serializers.ValidationError({
                    "sale_price": "Sale price must be less than regular price"
                })
        
        # Validate sizes format
        sizes = data.get('sizes', {})
        if not isinstance(sizes, dict):
            raise serializers.ValidationError({
                "sizes": "Sizes must be provided as a dictionary"
            })
        
        valid_sizes = {'S', 'M', 'L'}  # Add more sizes if needed
        for size, quantity in sizes.items():
            if size not in valid_sizes:
                raise serializers.ValidationError({
                    "sizes": f"Invalid size: {size}. Valid sizes are: {', '.join(valid_sizes)}"
                })
            if not isinstance(quantity, int) or quantity < 0:
                raise serializers.ValidationError({
                    "sizes": f"Quantity for size {size} must be a non-negative integer"
                })
        
        return data

class ProductDetailSerializer(ProductBaseSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
             'is_sale',
            'sale_price', 'category', 'images', 'reviews',
            'average_rating', 'ratings_breakdown', 'review_count', 
            'available_sizes', 'in_stock', 'availability_status', 
            'related_products', 'created_at', 'updated_at'
        ]

    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category
        ).exclude(
            id=obj.id
        ).order_by(
            '-created_at'
        )[:4]
        return ProductSerializer(related, many=True, context=self.context).data