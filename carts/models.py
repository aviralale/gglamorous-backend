from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(User, related_name='carts', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=3)  # Size field without static choices.
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.size}) x {self.quantity}"

    def clean(self):
        """
        Override clean method to validate size selection based on product's available sizes.
        """
        available_sizes = self.product.sizes.keys()  # Get available sizes from the product.
        if self.size not in available_sizes:
            raise ValueError(f"Size '{self.size}' is not available for {self.product.name}. Please select a valid size.")
