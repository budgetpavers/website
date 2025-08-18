"""
URL configuration for wall_quote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for wall_quote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from quotes import views
from quotes.admin import delivery_calendar_view, delivery_events

"""
URL configuration for wall_quote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for wall_quote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from quotes import views
from quotes.admin import delivery_calendar_view, delivery_events

urlpatterns = [
    # ============================================================================
    # ADMIN URLS
    # ============================================================================
    path('admin/', admin.site.urls),
    path("admin/delivery-calendar/", admin.site.admin_view(delivery_calendar_view), name="delivery_calendar"),
    path("admin/delivery-events/", admin.site.admin_view(delivery_events), name="delivery_events"),

    # ============================================================================
    # MAIN SITE PAGES
    # ============================================================================
    path("", views.homepage, name="homepage"),

    # ============================================================================
    # PRODUCT SYSTEM
    # ============================================================================
    path("our-range/", views.our_range, name="our_range"),
    path("our-range/<slug:slug>/", views.product_detail, name="product_detail"),

    # ============================================================================
    # AJAX ENDPOINTS (Essential for frontend functionality)
    # ============================================================================
    path('get-products-ajax/', views.get_products_ajax, name='get_products_ajax'),
    path('get-product-variants/<int:product_id>/', views.get_product_variants_ajax, name='get_product_variants_ajax'),

    # ============================================================================
    # UNIFIED AJAX API (NEW OPTIMIZED ENDPOINT)
    # ============================================================================
    path("unified-product-api/", views.unified_product_api, name="unified_product_api"),

    # ============================================================================
    # CART MANAGEMENT
    # ============================================================================
    path("cart/", views.cart_view, name="cart_view"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path('add-to-cart-modern/<int:product_id>/', views.add_to_cart_modern, name='add_to_cart_modern'),
    path("remove-from-cart/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update-cart/", views.update_cart, name="update_cart"),

    # ============================================================================
    # CONTENT PAGES
    # ============================================================================
    path("faq/", views.faq_view, name="faq"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),

    # ============================================================================
    # CHECKOUT & PAYMENT
    # ============================================================================
    path("checkout/", views.checkout_view, name="checkout"),
    path("calculate-delivery/", views.calculate_delivery, name="calculate_delivery"),
    path("create-payment-intent/", views.create_payment_intent, name="create_payment_intent"),
    path("process-order/", views.process_order, name="process_order"),
    path("order-confirmation/<str:order_number>/", views.order_confirmation, name="order_confirmation"),

    # ============================================================================
    # DELIVERY SLOTS
    # ============================================================================
    path("get-delivery-slots/", views.get_delivery_slots, name="get_delivery_slots"),

    # ============================================================================
    # DISCOUNT SYSTEM
    # ============================================================================
    path("apply-discount/", views.apply_discount, name="apply_discount"),
    path("remove-discount/", views.remove_discount, name="remove_discount"),

    # ============================================================================
    # LEGACY PRODUCT ENDPOINTS (kept for compatibility)
    # ============================================================================
    path('get-product-variants/<int:product_id>/', views.get_product_variants, name='get_product_variants'),
    path('add-to-cart-variant/<int:variant_id>/', views.add_to_cart_variant, name='add_to_cart_variant'),

    # ============================================================================
    # UTILITY & DEBUG ENDPOINTS
    # ============================================================================
    path("test-email/", views.test_email, name="test_email"),
    path("health-check/", views.health_check, name="health_check"),
    path('check-cart-steel/', views.check_cart_steel, name='check_cart_steel'),
    path('debug-cart/', views.debug_cart_contents, name='debug_cart_contents'),

# Add these to test what's happening
    path('debug/products/', views.check_database_products, name='debug_products'),
    path('debug/grouping/', views.debug_product_grouping, name='debug_grouping'),
    path('debug/range/', views.our_range_debug, name='debug_range'),
    path('debug/group/', views.debug_specific_group, name='debug_group'),

    path('debug-subcategory/', views.debug_subcategory_filtering, name='debug_subcategory'),


    # ============================================================================
    # DEBUG ENDPOINTS (only in development)
    # ============================================================================
]

# Add debug endpoints only in development
if settings.DEBUG:
    urlpatterns += [
        path('debug-product/<str:slug>/', views.debug_product_detail, name='debug_product_detail'),
    ]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)











