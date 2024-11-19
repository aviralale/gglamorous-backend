from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_name', 'street_name', 'city', 'is_default', 'recipient_name', 'phone_number']
    list_filter = ['city', 'is_default']
    search_fields = ['user__email', 'address_name', 'street_name', 'recepient_name', 'phone_number']
    # autocomplete_fields = ['user']  # Use autocomplete for user field to optimize query loading
    # readonly_fields = ['user']  # Make the user field read-only if you don't want it to be modified in admin

    def get_queryset(self, request):
        """
        Override to use 'select_related' to optimize queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related('user')  # Optimize the query by prefetching related user data
