from rest_framework import serializers
from orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_orders = serializers.ListField()
    sales_over_time = serializers.ListField()
    top_products = serializers.ListField()
    customer_growth = serializers.ListField()

class RecentOrderSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'total_amount', 'status', 'created_at']
    
    def get_customer(self, obj):
        return obj.user.get_full_name() or obj.user.email