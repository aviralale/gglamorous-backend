from rest_framework import viewsets, permissions
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Automatically set the cart based on the authenticated user or create a new one if it doesn't exist.
        """
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)
        serializer.save(cart=cart)