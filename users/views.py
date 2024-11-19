from rest_framework import viewsets, permissions
from .models import Address
from .serializers import AddressSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Assign the logged-in user to the address
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='me')
    def get_user_addresses(self, request):
        # Filter addresses by the current logged-in user
        user_addresses = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(user_addresses, many=True)
        return Response(serializer.data)
