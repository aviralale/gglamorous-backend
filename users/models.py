from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    address_name = models.CharField(max_length=255)
    street_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    recepient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.email} - {self.street_name}, {self.city} received by {self.recepient_name}"
