from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Prefetch, Q
from random import randint
from django.core.cache import cache
from .models import Category, Product, ProductImage, Review
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    ReviewSerializer,
    ProductDetailSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=True, methods=['GET'])
    def products(self, request, pk=None):
        """
        Get all products for a specific category
        """
        category = self.get_object()
        products = Product.objects.filter(category=category).select_related(
            'category'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.all()),
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        )
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'category__name']

    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.all()),
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        )

        # Search query parameter
        search_query = self.request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) 
            )

        # Filter by category
        category_slug = self.request.query_params.get('category_slug')
        category_id = self.request.query_params.get('category_id')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        elif category_id:
            queryset = queryset.filter(category_id=category_id)

        # Apply other filters
        if self.action == 'new_products':
            new_threshold = timezone.now() - timedelta(days=21)
            queryset = queryset.filter(created_at__gte=new_threshold)
        elif self.action == 'on_sale':
            queryset = queryset.filter(is_sale=True)
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(Product, slug=kwargs['slug'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'category__name']

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.all()),
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        )

        # Search query parameter
        search_query = self.request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # Filter by category
        category_slug = self.request.query_params.get('category_slug')
        category_id = self.request.query_params.get('category_id')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        elif category_id:
            queryset = queryset.filter(category_id=category_id)

        # Apply other filters
        if self.action == 'new_products':
            new_threshold = timezone.now() - timedelta(days=21)
            queryset = queryset.filter(created_at__gte=new_threshold)
        elif self.action == 'on_sale':
            queryset = queryset.filter(is_sale=True)
            
        return queryset

    def get_serializer_class(self):
        if self.action in ['retrieve', 'product_of_the_day']:
            return ProductDetailSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['GET'])
    def product_of_the_day(self, request):
        """
        Returns a randomly selected product of the day.
        The product remains the same throughout the day and changes at midnight.
        """
        cache_key = 'product_of_the_day'
        cached_product = cache.get(cache_key)

        if cached_product is None:
            # Get total number of products
            product_count = Product.objects.count()
            if product_count == 0:
                return Response(
                    {"error": "No products available"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get a random product
            random_index = randint(0, product_count - 1)
            product = Product.objects.select_related('category').prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.all()),
                Prefetch('reviews', queryset=Review.objects.select_related('user'))
            )[random_index]

            # Cache the product ID for 24 hours (86400 seconds)
            cache.set(cache_key, product.id, 86400)
        else:
            # Retrieve the cached product
            product = Product.objects.select_related('category').prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.all()),
                Prefetch('reviews', queryset=Review.objects.select_related('user'))
            ).get(id=cached_product)

        serializer = self.get_serializer(product, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def new_products(self, request):
        """
        Return products created within the last 21 days
        """
        products = self.get_queryset()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def on_sale(self, request):
        """
        Return products that are currently on sale
        """
        products = self.get_queryset()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def by_category(self, request):
        """
        Get products filtered by category slug (required)
        """
        category_slug = request.query_params.get('category_slug')
        if not category_slug:
            return Response(
                {"error": "category_slug parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        products = self.get_queryset()
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def search(self, request):
        """
        Search products with extended search capabilities
        """
        query = request.query_params.get('q')
        if not query:
            return Response(
                {"error": "Search query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        products = self.get_queryset()
        
        # Additional filters can be applied together with search
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        if min_price:
            products = products.filter(price__gte=float(min_price))
        if max_price:
            products = products.filter(price__lte=float(max_price))
            
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['comment', 'user__username']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def product_reviews(self, request):
        product_slug = request.query_params.get('product_slug')
        if not product_slug:
            return Response(
                {"error": "Product slug is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the product using the slug
        product = get_object_or_404(Product, slug=product_slug)
        
        # Filter reviews by the retrieved product
        reviews = self.queryset.filter(product=product)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)