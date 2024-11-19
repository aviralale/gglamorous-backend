from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import DashboardCache
from .serializers import DashboardStatsSerializer, RecentOrderSerializer
import json
from orders.models import Order
from products.models import Product
from account.models import User

class DashboardViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def _get_cached_stats(self, key):
        """Get cached statistics if they exist and are recent"""
        try:
            cache = DashboardCache.objects.get(key=key)
            if timezone.now() - cache.last_updated < timedelta(minutes=15):
                return cache.value
        except DashboardCache.DoesNotExist:
            pass
        return None

    def _cache_stats(self, key, value):
        """Cache statistics"""
        DashboardCache.objects.update_or_create(
            key=key,
            defaults={'value': value}
        )

    def _serialize_value(self, obj):
        """Helper method to serialize date and decimal objects in querysets"""
        if isinstance(obj, dict):
            return {
                key: self._serialize_value(value)
                for key, value in obj.items()
            }
        if hasattr(obj, 'isoformat'):  # For datetime/date objects
            return obj.isoformat()
        if isinstance(obj, Decimal):    # For Decimal objects
            return float(obj)
        return obj

    @action(detail=False, methods=['get'])
    def stats(self, request):
        # Try to get cached stats
        cached_stats = self._get_cached_stats('dashboard_stats')
        if cached_stats:
            return Response(cached_stats)

        # Calculate current statistics
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Basic stats
        total_orders = Order.objects.count()
        total_products = Product.objects.count()
        total_customers = User.objects.filter(is_staff=False).count()
        total_revenue = Order.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # Recent orders
        recent_orders = Order.objects.select_related('user').order_by(
            '-created_at'
        )[:10]
        recent_orders_data = RecentOrderSerializer(recent_orders, many=True).data

        # Sales over time
        sales_over_time = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('date')
        
        # Serialize dates and decimals in sales over time
        sales_over_time_data = [self._serialize_value(item) for item in sales_over_time]

        # Top products
        top_products = Product.objects.annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')[:5].values('name', 'order_count')

        # Customer growth
        customer_growth = User.objects.filter(
            is_staff=False,
            date_joined__gte=start_date
        ).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Serialize dates in customer growth
        customer_growth_data = [self._serialize_value(item) for item in customer_growth]

        stats = {
            'total_orders': total_orders,
            'total_products': total_products,
            'total_customers': total_customers,
            'total_revenue': float(total_revenue),
            'recent_orders': recent_orders_data,
            'sales_over_time': sales_over_time_data,
            'top_products': list(top_products),
            'customer_growth': customer_growth_data
        }

        # Cache the results
        self._cache_stats('dashboard_stats', stats)

        return Response(stats)

    @action(detail=False, methods=['get'])
    def sales_analytics(self, request):
        cached_stats = self._get_cached_stats('sales_analytics')
        if cached_stats:
            return Response(cached_stats)

        # Get parameters
        period = request.query_params.get('period', '30')  # days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=int(period))

        # Sales by category
        sales_by_category = Order.objects.filter(
            created_at__gte=start_date
        ).values(
            'items__product__category__name'
        ).annotate(
            total=Sum('total_amount')
        ).order_by('-total')

        # Serialize decimal values
        sales_by_category_data = [self._serialize_value(item) for item in sales_by_category]

        # Sales by payment method
        sales_by_payment = Order.objects.filter(
            created_at__gte=start_date
        ).values(
            'payment_method'
        ).annotate(
            total=Sum('total_amount'),
            count=Count('id')
        )

        # Serialize decimal values
        sales_by_payment_data = [self._serialize_value(item) for item in sales_by_payment]

        analytics = {
            'sales_by_category': sales_by_category_data,
            'sales_by_payment': sales_by_payment_data,
        }

        self._cache_stats('sales_analytics', analytics)
        return Response(analytics)