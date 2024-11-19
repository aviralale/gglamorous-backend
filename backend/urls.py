from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("public/api/", include("account.urls")),
    path('public/api/', include('users.urls')),
    path('public/api/', include('products.urls')),
    path('public/api/', include('orders.urls')),
    path('public/api/', include('carts.urls')),
    path('public/api/', include('wishlists.urls')),
    path('public/api/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)