from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name='wishlists', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='WishlistItem')  # Use 'through' to define intermediary model
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist of {self.user.email}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='wishlist_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlist_items', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True, null=True)  # Store size as a string (e.g., 'S', 'M', 'L')

    def __str__(self):
        return f"{self.product.name} ({self.size}) in wishlist of {self.wishlist.user.email}"
