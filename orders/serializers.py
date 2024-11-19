# orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductSerializer
from users.serializers import AddressSerializer
from account.serializers import UserSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    # Use the nested ProductSerializer to display product details
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressSerializer( read_only=True)
    user = UserSerializer()

    class Meta:
        model = Order
        fields = ['id', 'user', 'address', 'total_amount', 'payment_method', 'payment_status', 'status', 'created_at', 'items']

class OrderCreateSerializer(serializers.ModelSerializer):
    products = serializers.ListField(child=serializers.DictField(), write_only=True)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, required=True)

    class Meta:
        model = Order
        fields = ['address', 'products', 'payment_method']

    def create(self, validated_data):
        products = validated_data.pop('products')
        order = super().create(validated_data)

        return order
