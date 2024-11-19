from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_name = models.CharField(max_length=100)
    recipient_name = models.CharField(max_length=100, null=True)
    street_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_name} - {self.user.email}"
