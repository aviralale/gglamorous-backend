from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from products.models import Product
from users.models import Address

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """Handle order creation without stock deduction."""
        user = self.request.user
        data = self.request.data
        delivery_charge = 100

        payment_method = data.get('payment_method', 'COD')
        products = data.get('products', [])

        try:
            address = Address.objects.get(id=data['address'], user=user)
        except Address.DoesNotExist:
            return Response({'error': 'Invalid address'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = 0
        for item in products:
            product_id = item['product']
            quantity = item['stock']

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Product with ID {product_id} not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            item_price = product.sale_price if product.is_sale and product.sale_price else product.price
            total_amount += item_price * quantity + delivery_charge

        with transaction.atomic():
            # Explicitly set payment_status and initial order status
            order = serializer.save(
                user=user,
                address=address,
                total_amount=total_amount,
                payment_status='Pending',  # Ensure this is set
                status='Pending'  # Ensure this is set
            )

            for item in products:
                product = Product.objects.get(id=item['product'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['stock']
                )

        return Response(
            {'message': 'Order created successfully', 'order_id': order.id},
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        """Handle partial updates with proper status handling."""
        instance = self.get_object()
        
        # Get the current values
        previous_payment_status = instance.payment_status
        previous_status = instance.status
        
        # Get the new values from request
        new_payment_status = request.data.get('payment_status', previous_payment_status)
        new_status = request.data.get('status', previous_status)

        with transaction.atomic():
            # First update the order instance with new values
            instance.payment_status = new_payment_status
            instance.status = new_status

            # If payment status is changing to 'Paid', handle stock deduction
            if previous_payment_status != 'Paid' and new_payment_status == 'Paid':
                for item in instance.items.all():
                    product = item.product
                    if product.stock < item.quantity:
                        transaction.set_rollback(True)
                        return Response(
                            {'error': f'Not enough stock for {product.name}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    product.stock -= item.quantity
                    product.save()

            # Save the instance with all updates
            instance.save()

            # Serialize and return the updated instance
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_orders(self, request):
        """List orders for the authenticated user."""
        user_orders = self.queryset.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(user_orders, many=True)
        return Response(serializer.data)