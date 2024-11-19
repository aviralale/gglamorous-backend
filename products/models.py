from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    sizes = models.JSONField(default=dict)
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # Only set slug if not already set.
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def available(self):
        """
        Check if the product is available for purchase:
        - Must have stock > 0
        - Must have at least one size with stock
        """
        if self.stock <= 0:
            return False
            
        # Check if any size has stock
        return any(quantity > 0 for quantity in self.sizes.values())
        
    @property
    def current_price(self):
        """Return the sale price if on sale, otherwise regular price"""
        if self.is_sale and self.sale_price:
            return self.sale_price
        return self.price

    # Optional: Add a method to check stock for specific size
    def available_in_size(self, size):
        """Check if product is available in specific size"""
        return size in self.sizes and self.sizes[size] > 0

    # Optional: Add a method to update stock for a specific size
    def update_size_stock(self, size, quantity):
        """Update stock for a specific size"""
        if size in self.sizes:
            self.sizes[size] = max(0, quantity)  # Prevent negative stock
            self.stock = sum(self.sizes.values())  # Update total stock
            self.save()

    @property
    def is_new(self):
        """Check if product is new (created within the last 21 days)"""
        return (timezone.now() - self.created_at).days <= 21


    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image of {self.product.name}"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    quality_rating = models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    value_rating = models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    size = models.CharField(max_length=3)  # No static choices here.
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'user']  # Each user can review a product only once.

    def __str__(self):
        return f"Review of {self.product.name} by {self.user.email}"