# orders/views.py

import requests
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
        if self.action in ['create', 'update']:
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """Override to handle payment integration during order creation."""
        user = self.request.user
        data = self.request.data

        payment_method = data.get('payment_method', 'COD')
        products = data.get('products', [])
        payment_token = data.get('payment_token', None)  # For Khalti payments
        transaction_id = data.get('transaction_id', None)  # For eSewa payments

        # Retrieve and validate address
        try:
            address = Address.objects.get(id=data['address'], user=user)
        except Address.DoesNotExist:
            return Response({'error': 'Invalid address'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the total order amount
        total_amount = sum(item['price'] * item['quantity'] for item in products)

        # Start a transaction to ensure atomicity
        with transaction.atomic():
            order = serializer.save(user=user, address=address, total_amount=total_amount)

            # Create order items
            for item in products:
                product = Product.objects.get(id=item['product'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item['quantity'],
                    price=item['price']
                )

            # Handle payment for Khalti
            if payment_method == 'Khalti':
                if not payment_token:
                    return Response({'error': 'Payment token is required for Khalti payment'}, status=status.HTTP_400_BAD_REQUEST)

                response = requests.post(
                    'https://khalti.com/api/v2/payment/verify/',
                    headers={'Authorization': 'Key YOUR_KHALTI_SECRET_KEY'},
                    data={
                        'token': payment_token,
                        'amount': int(total_amount * 100)  # Convert to paisa
                    }
                )

                if response.status_code == 200:
                    order.payment_status = 'Paid'
                else:
                    return Response({'error': 'Khalti payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

            # Handle payment for eSewa
            elif payment_method == 'eSewa':
                if not transaction_id:
                    return Response({'error': 'Transaction ID is required for eSewa payment'}, status=status.HTTP_400_BAD_REQUEST)

                esewa_verify_url = 'https://uat.esewa.com.np/epay/transrec'
                esewa_data = {
                    'amt': total_amount,
                    'rid': transaction_id,
                    'pid': f'order-{order.id}',
                    'scd': 'YOUR_ESEWA_MERCHANT_CODE',
                }

                esewa_response = requests.post(esewa_verify_url, data=esewa_data)

                # Check if eSewa response is successful
                if 'Success' in esewa_response.text:
                    order.payment_status = 'Paid'
                    order.transaction_id = transaction_id
                else:
                    return Response({'error': 'eSewa payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

            # If payment is COD, mark as 'Pending' and save
            order.save()

        return Response({'message': 'Order created successfully', 'order_id': order.id}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def user_orders(self, request):
        """Custom action to list orders for the authenticated user."""
        user_orders = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(user_orders, many=True)
        return Response(serializer.data)
