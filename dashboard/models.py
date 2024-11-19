from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count
from orders.models import Order
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardCache(models.Model):
    """Cache for dashboard statistics to avoid heavy computations"""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['key']),
        ]