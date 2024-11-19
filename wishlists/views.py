from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, WishlistItemSerializer, WishlistCreateItemSerializer
from products.models import Product

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]  # Accept JSON, Form, and MultiPart form-data

    def get_queryset(self):
        """Filter wishlist by logged-in user."""
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Assign the user to the wishlist."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly], parser_classes=[JSONParser, FormParser, MultiPartParser])
    def add_item(self, request):
        """Custom action to add an item to the user's wishlist with form-data support."""
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistCreateItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(wishlist=wishlist)
            return Response({'message': 'Item added to wishlist successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'], permission_classes=[permissions.IsAuthenticatedOrReadOnly], parser_classes=[JSONParser, FormParser, MultiPartParser])
    def remove_item(self, request):
        """Custom action to remove an item from the user's wishlist with form-data support."""
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if not wishlist:
            return Response({'error': 'Wishlist not found'}, status=status.HTTP_404_NOT_FOUND)

        product_id = request.data.get('product_id')  # Read product_id from form-data
        try:
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product_id=product_id)
            wishlist_item.delete()
            return Response({'message': 'Item removed from wishlist successfully!'}, status=status.HTTP_204_NO_CONTENT)
        except WishlistItem.DoesNotExist:
            return Response({'error': 'Wishlist item not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def my_wishlist(self, request):
        """Custom action to retrieve the user's wishlist."""
        wishlist = self.get_queryset().first()
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)
