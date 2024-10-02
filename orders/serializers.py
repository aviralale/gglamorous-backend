# orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'address', 'total_amount', 'payment_method', 'payment_status', 'transaction_id', 'status', 'created_at', 'items']

class OrderCreateSerializer(serializers.ModelSerializer):
    products = serializers.ListField(child=serializers.DictField(), write_only=True)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, required=True)
    payment_token = serializers.CharField(max_length=255, required=False, write_only=True)
    transaction_id = serializers.CharField(max_length=100, required=False, write_only=True)

    class Meta:
        model = Order
        fields = ['address', 'products', 'payment_method', 'payment_token', 'transaction_id']

    def create(self, validated_data):
        products = validated_data.pop('products')
        order = super().create(validated_data)
        return order
