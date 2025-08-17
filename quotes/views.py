import os
import re
import pandas as pd
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from urllib.parse import parse_qs
import stripe
import json
from decimal import Decimal
from django.db.models import Q
from django.template.loader import render_to_string
from django.core.cache import cache

from .models import (
    QuoteRequest, Product, FAQ, BlogPost, Customer, Order, OrderItem,
    DeliverySlot, DiscountCode, DiscountUsage, ProductCategory,
    ProductGroup, ProductVariant, Brand
)
from .products_data import products  # Import the static products data


# ============================================================================
# PRODUCT GROUPING AND CATEGORIZATION HELPERS
# ============================================================================

class ProductGroupManager:
    """Centralized product grouping and filtering logic"""

    @staticmethod
    def get_main_category(category):
        """Convert database category to main category"""
        category_lower = category.lower()

        if 'sleeper' in category_lower and 'step' not in category_lower:
            return "Concrete Sleepers"
        elif 'ufp' in category_lower or 'plinth' in category_lower:
            return "Under Fence Plinths"
        elif 'steel' in category_lower:
            return "Galvanised Steel"
        elif 'step' in category_lower:
            return "Step Kits"
        elif 'accessor' in category_lower:
            return "Accessories"
        else:
            return "Other"

    @staticmethod
    def determine_product_subcategory(product):
        """Determine subcategory for any product"""
        main_category = ProductGroupManager.get_main_category(product.category)

        if main_category == "Concrete Sleepers":
            return ProductGroupManager.determine_sleeper_color_exact(product) or "Other Sleepers"
        elif main_category == "Under Fence Plinths":
            return ProductGroupManager.determine_ufp_color_exact(product) or "Other UFPs"
        elif main_category == "Galvanised Steel":
            return ProductGroupManager.determine_steel_product_exact(product) or "Other Steel"
        elif main_category == "Step Kits":
            return ProductGroupManager.determine_step_kit_exact(product) or "Other Step Kits"
        elif main_category == "Accessories":
            return ProductGroupManager.determine_accessory_exact(product) or "Other Accessories"
        else:
            return "Other"

    @staticmethod
    def determine_steel_product_exact(product):
        """Determine exact steel product type"""
        name_lower = product.name.lower()

        if '120ub65' in name_lower:
            return "120UB65 I Beam"
        elif '125x65' in name_lower and 'channel' in name_lower:
            return "125x65 C Channel"
        elif '150ub14' in name_lower:
            return "150UB14 I Beam"
        elif '150x75' in name_lower and 'channel' in name_lower:
            return "150x75 C Channel"
        return None

    @staticmethod
    def determine_sleeper_color_exact(product):
        """Determine exact sleeper color"""
        name_lower = product.name.lower()

        # Check for exact color combinations - order matters!
        if 'plain grey' in name_lower:
            return "Plain Grey"
        elif 'plain sandstone' in name_lower:
            return "Plain Sandstone"
        elif 'plain charcoal' in name_lower:
            return "Plain Charcoal"
        elif 'charcoal stackstone' in name_lower:
            return "Charcoal Stackstone"
        elif 'sandstone rockface' in name_lower:  # Check this BEFORE charcoal rockface
            return "Sandstone Rockface"
        elif 'charcoal rockface' in name_lower:
            return "Charcoal Rockface"
        elif 'woodgrain' in name_lower:
            return "Woodgrain"
        else:
            # Fallback logic - be more specific
            if 'stackstone' in name_lower:
                return "Charcoal Stackstone"
            elif 'rockface' in name_lower:
                if 'sandstone' in name_lower or '[sand]' in name_lower:
                    return "Sandstone Rockface"
                else:
                    return "Charcoal Rockface"
            elif 'grey' in name_lower or '[grey]' in name_lower:
                return "Plain Grey"
            elif 'sandstone' in name_lower or '[sand]' in name_lower:
                return "Plain Sandstone"
            elif 'charcoal' in name_lower or '[char]' in name_lower:
                return "Plain Charcoal"
            else:
                return "Plain Grey"  # Default

    @staticmethod
    def determine_ufp_color_exact(product):
        """Determine exact UFP color"""
        name_lower = product.name.lower()

        if '[grey]' in name_lower:
            return "Plain Grey UFPs"
        elif '[char]' in name_lower:
            return "Plain Charcoal UFPs"
        elif '[sand]' in name_lower:
            return "Plain Sandstone UFPs"
        elif 'stackstone' in name_lower:
            return "Charcoal Stackstone UFPs"
        return None

    @staticmethod
    def determine_step_kit_exact(product):
        """Determine exact step kit type and color"""
        name_lower = product.name.lower()

        if 'wide opening' in name_lower:
            if 'plain grey' in name_lower:
                return "Step Kits Wide Opening - Plain Grey"
            elif 'plain charcoal' in name_lower:
                return "Step Kits Wide Opening - Plain Charcoal"
            elif 'charcoal stackstone' in name_lower:
                return "Step Kits Wide Opening - Charcoal Stackstone"
            elif 'charcoal rockface' in name_lower:
                return "Step Kits Wide Opening - Charcoal Rockface"
            elif 'sandstone rockface' in name_lower:
                return "Step Kits Wide Opening - Sandstone Rockface"
            elif 'woodgrain' in name_lower:
                return "Step Kits Wide Opening - Woodgrain"
            else:
                return "Step Kits Wide Opening"
        elif 'tread' in name_lower:
            if 'plain sandstone' in name_lower:
                return "Step Kit Tread - Plain Sandstone"
            elif 'plain charcoal' in name_lower:
                return "Step Kit Tread - Plain Charcoal"
            elif 'plain grey' in name_lower:
                return "Step Kit Tread - Plain Grey"
            else:
                return "Step Kit Tread"
        else:
            return "Other Step Kits"

    @staticmethod
    def determine_accessory_exact(product):
        """Determine exact accessory type"""
        name_lower = product.name.lower()

        if 'chemical anchor glue' in name_lower and '300ml' in name_lower:
            return "Step Kit Chemical Anchor Glue"
        elif 'wheel stops' in name_lower and '1650' in name_lower:
            return "Wheel Stops"
        elif 'ag pipe' in name_lower and 'slotted sock' in name_lower:
            return "Ag Pipe - Slotted Sock"
        elif 'step kit brackets' in name_lower:
            return "Step Kit Brackets"
        elif 'fence bracket' in name_lower:
            return "Fence Brackets"
        elif 'wheel stop fixings' in name_lower:
            return "Wheel Stop Fixings"
        return None

    @staticmethod
    def extract_brand_from_product(product):
        """Extract brand from product based on category and name"""
        category = product.category.lower()
        name = product.name.lower()
        sku = getattr(product, 'sku', '') or ''

        # Check for Silvercrete indicators
        if 'silvercrete' in category or 'silvercrete' in name or '-sc' in sku.lower():
            return "Silvercrete"
        # Check for Outback Sleepers indicators
        elif 'outback' in category or 'outback' in name or '-os' in sku.lower():
            return "Outback Sleepers"
        # For steel and accessories, no brand needed
        elif any(term in category for term in ['steel', 'accessori', 'step']):
            return None
        return None

    @staticmethod
    def extract_product_details_for_filtering(product):
        """Extract detailed information from product for filtering"""
        details = {}
        name_lower = product.name.lower()

        # Extract brand
        details['brand'] = ProductGroupManager.extract_brand_from_product(product)

        # Extract length
        length_patterns = [
            r'(\d+\.?\d*)\s*m(?:\s|$|x)',  # e.g., "2.4m", "1.8m"
            r'(\d{3,4})\s*mm',  # e.g., "600mm", "1200mm"
            r'(\d{4})\s*(?:mm|x)',  # e.g., "2000mm", "2400x"
        ]

        for pattern in length_patterns:
            match = re.search(pattern, name_lower)
            if match:
                value = float(match.group(1))
                if value > 100:  # Likely millimeters
                    details['length'] = f"{value / 1000:.1f}m"
                else:  # Likely meters
                    details['length'] = f"{value:.1f}m"
                break

        # Extract height
        height_patterns = [
            r'(?:x|×)(\d{2,3})(?:x|×|mm|\s)',  # e.g., "x200x", "x150mm"
            r'(\d{2,3})\s*(?:high|height)',  # e.g., "200 high"
        ]

        for pattern in height_patterns:
            match = re.search(pattern, name_lower)
            if match:
                height = int(match.group(1))
                if 'tapered' in name_lower:
                    details['height'] = f"{height} tapered to 100mm"
                else:
                    details['height'] = f"{height}mm"
                break

        # Extract thickness
        thickness_patterns = [
            r'(?:x|×)(\d{2,3})(?:mm|\s|$)',  # e.g., "x75mm", "x100 "
            r'(\d{2,3})\s*(?:thick|mm)',  # e.g., "80 thick", "100mm"
        ]

        for pattern in thickness_patterns:
            match = re.search(pattern, name_lower)
            if match:
                thickness = int(match.group(1))
                if 'rebated' in name_lower and thickness == 65:
                    details['thickness'] = "Rebated 65 to 50mm"
                else:
                    details['thickness'] = f"{thickness}mm"
                break

        # Extract size for step kits
        size_patterns = [r'(2\.0m|2\.4m)', r'(\d+\.?\d*m)']
        for pattern in size_patterns:
            match = re.search(pattern, name_lower)
            if match:
                details['size'] = match.group(1)
                break

        # Extract rebated info
        details['rebated'] = 'Yes' if 'rebated' in name_lower else 'No'

        # Extract smooth finish info
        if 'double-sided' in name_lower or 'double sided' in name_lower:
            details['smooth_finish'] = 'Double-sided'
        elif 'one-sided' in name_lower or 'single-sided' in name_lower:
            details['smooth_finish'] = 'One-sided'

        # Extract accessory-specific details
        if 'steel fence' in name_lower:
            details['type'] = 'Steel Fence [700x48x5mm]'
        elif 'timber fence' in name_lower:
            details['type'] = 'Timber Fence [700x70x8mm]'
        elif 'asphalt' in name_lower:
            details['type'] = 'Asphalt'
        elif 'concrete' in name_lower:
            details['type'] = 'Concrete'

        if '3pk' in name_lower or '3 pack' in name_lower:
            details['pack_size'] = '[300mm 3pk]'
        elif '12pk' in name_lower or '12 pack' in name_lower:
            details['pack_size'] = '[300mm 12pk]'

        return details

    @staticmethod
    def group_products_efficiently(products):
        """Efficiently group products avoiding duplicates"""
        product_groups = {}

        for product in products:
            main_category = ProductGroupManager.get_main_category(product.category)
            subcategory = ProductGroupManager.determine_product_subcategory(product)
            brand = ProductGroupManager.extract_brand_from_product(product)

            # Create a unique group key for identical products (different sizes)
            group_key = f"{main_category}_{subcategory}_{brand or 'nobrand'}"

            if group_key not in product_groups:
                product_groups[group_key] = {
                    'products': [],
                    'main_category': main_category,
                    'subcategory': subcategory,
                    'brand': brand,
                    'representative_product': product,  # Use first product as representative
                    'min_price': product.price,
                    'variant_count': 0
                }

            product_groups[group_key]['products'].append(product)
            product_groups[group_key]['variant_count'] += 1

            # Update min price
            if product.price < product_groups[group_key]['min_price']:
                product_groups[group_key]['min_price'] = product.price
                product_groups[group_key]['representative_product'] = product

        return product_groups

    @staticmethod
    def apply_category_filter(products, category_filter):
        """Apply category filtering"""
        if category_filter == 'concrete-sleepers':
            return products.filter(Q(category__icontains='Concrete Sleepers') | Q(category__icontains='Sleeper'))
        elif category_filter == 'under-fence-plinths':
            return products.filter(Q(category__icontains='Under Fence Plinths') | Q(category__icontains='UFP'))
        elif category_filter == 'galvanised-steel':
            return products.filter(Q(category__icontains='Steel'))
        elif category_filter == 'accessories':
            return products.filter(Q(category__icontains='Accessories') | Q(category__icontains='Wheel Stops'))
        elif category_filter == 'step-kits':
            return products.filter(Q(category__icontains='Step'))
        else:
            return products


# ============================================================================
# DELIVERY AND STEEL DETECTION HELPERS
# ============================================================================

def is_steel_product(product):
    """Determine if a product is a steel product"""
    if not product:
        return False

    category_lower = product.category.lower()
    name_lower = product.name.lower()

    # Check category first
    if 'steel' in category_lower:
        return True

    # Check product name for steel indicators
    steel_indicators = [
        'galv steel', 'galvanised steel', 'i beam', 'c channel',
        'ub65', 'ub14', '120ub', '150ub', 'channel', 'beam',
        'galv', 'steel post', 'h post', 'c post'
    ]

    return any(indicator in name_lower for indicator in steel_indicators)


def determine_if_steel_order(cart):
    """Check if cart contains any steel products"""
    for cart_key, quantity in cart.items():
        if '-' in cart_key:
            product_id_str, thickness = cart_key.split('-', 1)
        else:
            product_id_str = cart_key

        try:
            product = Product.objects.get(id=product_id_str, is_active=True)
            if is_steel_product(product):
                return True
        except Product.DoesNotExist:
            continue

    return False


# ============================================================================
# MAIN VIEWS
# ============================================================================

def homepage(request):
    if request.method == "POST":
        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone = request.POST.get('customer_phone')
        address = request.POST.get('delivery_address')
        postcode = request.POST.get('postcode')
        preferred_date = request.POST.get('date')
        calculator_type = request.POST.get('calculator_type')
        notes = request.POST.get('calculated_results')
        custom_message = request.POST.get('custom_message', '')

        wall_length = request.POST.get('wall_length')
        wall_height = request.POST.get('wall_height')
        fence_length = request.POST.get('fence_length')
        plinths_per_panel = request.POST.get('plinths_per_panel')

        excel_path = os.path.join(settings.BASE_DIR, 'SA Postcode Zone List - Latif.xlsx')
        df = pd.read_excel(excel_path)

        delivery_zone = "Unknown"
        delivery_cost = 0.0

        try:
            row = df.loc[df['Postcode'].astype(str) == str(postcode)].iloc[0]
            delivery_zone = row['Zone'].strip()
            if delivery_zone.lower() == 'metro':
                delivery_cost = 68.18
            elif delivery_zone.lower() == 'outer metro':
                delivery_cost = 81.80
        except Exception:
            pass

        QuoteRequest.objects.create(
            customer_name=name,
            customer_email=email,
            phone=phone,
            delivery_address=f"{address}, {postcode}",
            preferred_date=preferred_date,
            created_at=timezone.now(),
            status='pending',
            calculator_type=calculator_type,
            wall_length=wall_length or None,
            wall_height=wall_height or None,
            fence_length=fence_length or None,
            plinths_per_panel=plinths_per_panel or None,
            estimated_cost=None,
            delivery_zone=delivery_zone,
            delivery_cost=delivery_cost,
            custom_message=custom_message,
        )

        return render(request, 'thank_you.html', {
            'name': name,
            'delivery_zone': delivery_zone,
            'delivery_cost': delivery_cost,
        })

    return render(request, 'homepage.html')


def our_range(request):
    """Optimized product display with proper grouping info"""
    try:
        category_filter = request.GET.get('category', '')
        search_query = request.GET.get('search', '')

        # Get all active products
        products_qs = Product.objects.filter(is_active=True).order_by('category', 'name')
        print(f"🔍 Starting with {products_qs.count()} active products")

        # Apply category filter if provided
        if category_filter and category_filter != 'all':
            products_qs = ProductGroupManager.apply_category_filter(products_qs, category_filter)
            print(f"🔍 After category filter '{category_filter}': {products_qs.count()} products")

        # Apply search filter if provided
        if search_query:
            products_qs = products_qs.filter(
                Q(name__icontains=search_query) |
                Q(category__icontains=search_query)
            )
            print(f"🔍 After search filter '{search_query}': {products_qs.count()} products")

        # Use efficient grouping
        product_groups = ProductGroupManager.group_products_efficiently(products_qs)
        print(f"🔍 Created {len(product_groups)} product groups")

        # Convert groups to display format with proper variant info
        grouped_products = []
        for group_key, group_data in product_groups.items():
            try:
                representative = group_data['representative_product']

                # Handle image field properly
                image_url = None
                if hasattr(representative, 'image') and representative.image:
                    try:
                        image_url = representative.image.url
                    except (ValueError, AttributeError):
                        image_url = None

                product_data = {
                    'id': representative.id,
                    'name': representative.name,
                    'price': representative.price,
                    'category': group_data['main_category'],
                    'subcategory': group_data['subcategory'],
                    'brand': group_data['brand'] or "",
                    'image': image_url,
                    'sku': getattr(representative, 'sku', ''),
                    'category_slug': group_data['main_category'].lower().replace(' ', '-'),
                    'subcategory_slug': group_data['subcategory'].lower().replace(' ', '-').replace('/', '-'),
                    'brand_slug': (group_data['brand'] or "").lower().replace(' ', '-'),
                    'variant_count': group_data['variant_count'],  # This is the key field
                    'group_key': group_key  # For debugging
                }
                grouped_products.append(product_data)
                print(f"  ✅ Group: {representative.name} - {group_data['variant_count']} variants")
            except Exception as e:
                print(f"❌ Error processing group {group_key}: {str(e)}")
                continue

        print(f"✅ Returning {len(grouped_products)} product groups")

        # Filter options
        filter_options = {
            'categories': [
                {'name': 'Concrete Sleepers', 'slug': 'concrete-sleepers', 'icon': 'fas fa-building'},
                {'name': 'Under Fence Plinths', 'slug': 'under-fence-plinths', 'icon': 'fas fa-layer-group'},
                {'name': 'Galvanised Steel', 'slug': 'galvanised-steel', 'icon': 'fas fa-industry'},
                {'name': 'Step Kits', 'slug': 'step-kits', 'icon': 'fas fa-stairs'},
                {'name': 'Accessories', 'slug': 'accessories', 'icon': 'fas fa-tools'},
            ]
        }

        context = {
            'grouped_products': grouped_products,
            'filter_options': filter_options,
            'current_category': category_filter,
            'current_search': search_query,
            'total_products': len(grouped_products),
        }

        return render(request, 'our_range_modern.html', context)

    except Exception as e:
        print(f"❌ Error in our_range view: {str(e)}")
        import traceback
        traceback.print_exc()

        context = {
            'grouped_products': [],
            'filter_options': {
                'categories': [
                    {'name': 'Concrete Sleepers', 'slug': 'concrete-sleepers', 'icon': 'fas fa-building'},
                    {'name': 'Under Fence Plinths', 'slug': 'under-fence-plinths', 'icon': 'fas fa-layer-group'},
                    {'name': 'Galvanised Steel', 'slug': 'galvanised-steel', 'icon': 'fas fa-industry'},
                    {'name': 'Step Kits', 'slug': 'step-kits', 'icon': 'fas fa-stairs'},
                    {'name': 'Accessories', 'slug': 'accessories', 'icon': 'fas fa-tools'},
                ]
            },
            'current_category': category_filter,
            'current_search': search_query,
            'total_products': 0,
        }
        return render(request, 'our_range_modern.html', context)


# ============================================================================
# UNIFIED AJAX ENDPOINTS
# ============================================================================

@require_GET
def unified_product_api(request):
    """
    Unified AJAX endpoint for all product-related operations
    Handles: filtering, grouping, variants, options, and search
    """
    try:
        operation = request.GET.get('operation', 'filter')

        if operation == 'filter':
            return handle_product_filtering(request)
        elif operation == 'variants':
            return handle_product_variants(request)
        elif operation == 'options':
            return handle_product_options(request)
        elif operation == 'search':
            return handle_product_search(request)
        elif operation == 'specifications':
            return handle_product_specifications(request)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid operation'
            }, status=400)

    except Exception as e:
        print(f"❌ Error in unified_product_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def handle_product_filtering(request):
    """Handle product filtering with proper grouping maintained"""
    category = request.GET.get('category', '')
    subcategory = request.GET.get('subcategory', '')
    brand = request.GET.get('brand', '')
    search = request.GET.get('search', '')

    print(f"🔍 AJAX Filter: cat={category}, subcat={subcategory}, brand={brand}, search={search}")

    # Start with all active products
    products = Product.objects.filter(is_active=True)

    # Apply category filter
    if category and category != 'all':
        products = ProductGroupManager.apply_category_filter(products, category)

    # Apply search filter
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(category__icontains=search)
        )

    # Use efficient grouping BEFORE applying subcategory/brand filters
    product_groups = ProductGroupManager.group_products_efficiently(products)

    # Apply subcategory and brand filtering to groups
    filtered_groups = {}
    for group_key, group_data in product_groups.items():
        include_group = True

        # Apply subcategory filtering
        if subcategory and subcategory.strip():
            filter_subcategory = subcategory.lower().replace('-', ' ').strip()
            product_subcategory = group_data['subcategory'].lower().strip()

            if filter_subcategory not in product_subcategory and product_subcategory not in filter_subcategory:
                include_group = False

        # Apply brand filtering
        if brand and brand.strip():
            if not group_data['brand'] or group_data['brand'].lower() != brand.lower():
                include_group = False

        if include_group:
            filtered_groups[group_key] = group_data

    # Convert to organized products
    organized_products = []
    for group_key, group_data in filtered_groups.items():
        try:
            representative = group_data['representative_product']

            # Handle image field properly
            image_url = None
            if hasattr(representative, 'image') and representative.image:
                try:
                    image_url = representative.image.url
                except (ValueError, AttributeError):
                    image_url = None

            product_data = {
                'id': representative.id,
                'name': representative.name,
                'price': float(representative.price),
                'category': group_data['main_category'],
                'subcategory': group_data['subcategory'],
                'brand': group_data['brand'] or "",
                'image': image_url,
                'sku': getattr(representative, 'sku', ''),
                'category_slug': group_data['main_category'].lower().replace(' ', '-'),
                'subcategory_slug': group_data['subcategory'].lower().replace(' ', '-').replace('/', '-'),
                'brand_slug': (group_data['brand'] or "").lower().replace(' ', '-'),
                'variant_count': group_data['variant_count']  # Include variant count
            }
            organized_products.append(product_data)
        except Exception as e:
            print(f"❌ Error processing group {group_key}: {str(e)}")
            continue

    print(f"✅ AJAX returning {len(organized_products)} product groups")

    return JsonResponse({
        'success': True,
        'products': organized_products,
        'count': len(organized_products)
    })


def handle_product_variants(request):
    """Handle getting product variants for grouped products"""
    product_id = request.GET.get('product_id')

    if not product_id:
        return JsonResponse({
            'success': False,
            'error': 'Product ID required'
        }, status=400)

    try:
        base_product = Product.objects.get(id=product_id, is_active=True)
        main_category = ProductGroupManager.get_main_category(base_product.category)

        print(f"🔍 Loading variants for {base_product.name} (category: {main_category})")

        # Determine the product group characteristics
        if main_category == "Concrete Sleepers":
            color_group = ProductGroupManager.determine_sleeper_color_exact(base_product)
            brand = ProductGroupManager.extract_brand_from_product(base_product)
            group_criteria = {'color': color_group, 'brand': brand}
        elif main_category == "Under Fence Plinths":
            color_group = ProductGroupManager.determine_ufp_color_exact(base_product)
            brand = ProductGroupManager.extract_brand_from_product(base_product)
            group_criteria = {'color': color_group, 'brand': brand}
        elif main_category == "Galvanised Steel":
            steel_type = ProductGroupManager.determine_steel_product_exact(base_product)
            group_criteria = {'steel_type': steel_type}
        else:
            # For accessories and step kits, no variants expected
            return JsonResponse({
                'success': True,
                'variants': [],
                'has_variants': False
            })

        print(f"🔍 Group criteria: {group_criteria}")

        # Find all products that match the same group criteria
        all_products = Product.objects.filter(is_active=True)
        variants = []

        for product in all_products:
            product_main_category = ProductGroupManager.get_main_category(product.category)

            if product_main_category == main_category:
                should_include = False

                if main_category == "Concrete Sleepers":
                    product_color = ProductGroupManager.determine_sleeper_color_exact(product)
                    product_brand = ProductGroupManager.extract_brand_from_product(product)
                    if (product_color == group_criteria['color'] and
                        product_brand == group_criteria['brand']):
                        should_include = True

                elif main_category == "Under Fence Plinths":
                    product_color = ProductGroupManager.determine_ufp_color_exact(product)
                    product_brand = ProductGroupManager.extract_brand_from_product(product)
                    if (product_color == group_criteria['color'] and
                        product_brand == group_criteria['brand']):
                        should_include = True

                elif main_category == "Galvanised Steel":
                    product_steel_type = ProductGroupManager.determine_steel_product_exact(product)
                    if product_steel_type == group_criteria['steel_type']:
                        should_include = True

                if should_include:
                    details = ProductGroupManager.extract_product_details_for_filtering(product)

                    if main_category == "Galvanised Steel":
                        size_info = details.get('length', 'Unknown length')
                    else:
                        length = details.get('length', 'Unknown')
                        height = details.get('height', 'Unknown')
                        thickness = details.get('thickness', 'Unknown')
                        size_info = f"{length} × {height} × {thickness}"

                    variants.append({
                        'id': product.id,
                        'name': product.name,
                        'price': float(product.price),
                        'size_display': size_info,
                        'length': details.get('length', ''),
                        'height': details.get('height', ''),
                        'thickness': details.get('thickness', ''),
                    })

        # Sort variants by price
        variants.sort(key=lambda x: x['price'])
        has_variants = len(variants) > 1

        print(f"✅ Found {len(variants)} variants, has_variants: {has_variants}")

        return JsonResponse({
            'success': True,
            'variants': variants,
            'has_variants': has_variants,
            'base_product': {
                'id': base_product.id,
                'name': base_product.name,
                'price': float(base_product.price)
            }
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        print(f"❌ Error getting variants: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def handle_product_options(request):
    """Handle getting product configuration options"""
    group = request.GET.get('group', '')
    category = request.GET.get('category', '')

    # Start with all active products
    products = Product.objects.filter(is_active=True)

    # Filter by category
    if category == 'steel':
        products = products.filter(category__icontains='Steel')
    elif category == 'sleepers':
        products = products.filter(category__icontains='Sleepers')
    elif category == 'ufp':
        products = products.filter(category__icontains='UFP')

    # Filter by specific product type based on group
    if '120ub65' in group.lower():
        products = products.filter(name__icontains='120UB65')
    elif '125x65' in group.lower():
        products = products.filter(name__icontains='125x65')
    elif '150ub14' in group.lower():
        products = products.filter(name__icontains='150UB14')
    elif '150x75' in group.lower():
        products = products.filter(name__icontains='150x75')

    # Extract unique options from matching products
    lengths = set()
    heights = set()
    thicknesses = set()
    brands = set()

    for product in products:
        dimensions = ProductGroupManager.extract_product_details_for_filtering(product)
        if dimensions.get('length'):
            lengths.add(dimensions['length'])
        if dimensions.get('height'):
            heights.add(dimensions['height'])
        if dimensions.get('thickness'):
            thicknesses.add(dimensions['thickness'])
        if dimensions.get('brand'):
            brands.add(dimensions['brand'])

    # Sort options
    def sort_length_key(length_str):
        try:
            return float(length_str.replace('m', ''))
        except:
            return 999

    def sort_dimension_key(dim_str):
        try:
            return int(dim_str.replace('mm', '').split()[0])
        except:
            return 999

    return JsonResponse({
        'success': True,
        'lengths': sorted(list(lengths), key=sort_length_key),
        'heights': sorted(list(heights), key=sort_dimension_key),
        'thicknesses': sorted(list(thicknesses), key=sort_dimension_key),
        'brands': sorted(list(brands)),
        'count': products.count()
    })


def handle_product_search(request):
    """Handle product search with intelligent grouping"""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({
            'success': True,
            'products': [],
            'count': 0
        })

    # Search in product names and categories
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(category__icontains=query),
        is_active=True
    )

    # Use efficient grouping
    product_groups = ProductGroupManager.group_products_efficiently(products)

    # Convert to display format
    search_results = []
    for group_key, group_data in product_groups.items():
        representative = group_data['representative_product']

        search_results.append({
            'id': representative.id,
            'name': representative.name,
            'price': float(representative.price),
            'category': group_data['main_category'],
            'subcategory': group_data['subcategory'],
            'brand': group_data['brand'] or "",
            'variant_count': group_data['variant_count']
        })

    return JsonResponse({
        'success': True,
        'products': search_results,
        'count': len(search_results)
    })


def handle_product_specifications(request):
    """Handle finding exact product by specifications"""
    group = request.GET.get('group', '')
    brand = request.GET.get('brand', '')
    length = request.GET.get('length', '')
    height = request.GET.get('height', '')
    thickness = request.GET.get('thickness', '')

    # Start with all active products
    products = Product.objects.filter(is_active=True)

    # Apply category filtering based on group
    if 'sleepers' in group.lower():
        products = products.filter(category__icontains='Sleeper')

        # Filter by brand
        if brand == 'silvercrete':
            products = products.filter(category__icontains='Silvercrete')
        elif brand == 'outback':
            products = products.filter(category__icontains='Outback')

        # Filter by color based on group name
        if 'plain-grey' in group:
            products = products.filter(name__icontains='Plain Grey')
        elif 'plain-sandstone' in group:
            products = products.filter(name__icontains='Plain Sandstone')
        elif 'plain-charcoal' in group:
            products = products.filter(name__icontains='Plain Charcoal')
        elif 'charcoal-stackstone' in group:
            products = products.filter(name__icontains='Stackstone')
        elif 'charcoal-rockface' in group:
            products = products.filter(name__icontains='Rockface').filter(name__icontains='CHAR')
        elif 'sandstone-rockface' in group:
            products = products.filter(name__icontains='Rockface').filter(name__icontains='SAND')
        elif 'woodgrain' in group:
            products = products.filter(name__icontains='Woodgrain')

        # Convert UI selections to database format
        length_mm = convert_length_to_mm(length)
        height_mm = convert_dimension_to_mm(height)
        thickness_mm = convert_dimension_to_mm(thickness)

        # Look for exact dimension match in product name
        if length_mm and height_mm and thickness_mm:
            dimension_pattern = f"{length_mm}x{height_mm}x{thickness_mm}"
            matching_products = products.filter(name__icontains=dimension_pattern)

            if matching_products.exists():
                product = matching_products.first()
                return JsonResponse({
                    'success': True,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': f"{float(product.price):.2f}",
                        'sku': getattr(product, 'sku', ''),
                        'category': product.category,
                        'image_url': product.image.url if hasattr(product, 'image') and product.image else None
                    }
                })

    elif 'steel' in group.lower():
        products = products.filter(category__icontains='Steel')

        # Match steel type
        if '120ub65' in group.lower():
            products = products.filter(name__icontains='120UB65')
        elif '125x65' in group.lower():
            products = products.filter(name__icontains='125x65')
        elif '150ub14' in group.lower():
            products = products.filter(name__icontains='150UB14')
        elif '150x75' in group.lower():
            products = products.filter(name__icontains='150x75')

        # Match length
        if length:
            length_variations = [
                length,  # "2.4m"
                length.replace('m', ''),  # "2.4"
                length.replace('.', ''),  # "24m"
                str(int(float(length.replace('m', '')) * 1000)) + 'mm'  # "2400mm"
            ]

            for length_var in length_variations:
                matching_steel = products.filter(name__icontains=length_var)
                if matching_steel.exists():
                    product = matching_steel.first()
                    return JsonResponse({
                        'success': True,
                        'product': {
                            'id': product.id,
                            'name': product.name,
                            'price': f"{float(product.price):.2f}",
                            'sku': getattr(product, 'sku', ''),
                            'category': product.category,
                            'image_url': product.image.url if hasattr(product, 'image') and product.image else None
                        }
                    })

    # No match found
    return JsonResponse({
        'success': False,
        'message': f'No exact match found for {group}',
        'available_count': products.count(),
        'sample_products': [p.name for p in products[:3]]
    })


# ============================================================================
# CART MANAGEMENT
# ============================================================================

@require_POST
def add_to_cart_modern(request, product_id):
    """Modern add to cart with better response handling"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1

        # Get product from database
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            }, status=404)

        # Add to cart
        cart_key = str(product_id)
        cart = request.session.get('cart', {})
        cart[cart_key] = cart.get(cart_key, 0) + quantity
        request.session['cart'] = cart
        request.session.modified = True

        # Get cart total count
        total_items = sum(cart.values())

        return JsonResponse({
            'success': True,
            'message': f'Added {quantity}x {product.name} to cart!',
            'product_name': product.name,
            'price': float(product.price),
            'cart_total_items': total_items,
            'quantity_added': quantity
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid quantity'
        }, status=400)
    except Exception as e:
        print(f"❌ Add to cart error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to add product to cart'
        }, status=500)


def add_to_cart(request, product_id):
    """Legacy add to cart function"""
    if request.method == "POST":
        qty = request.POST.get('quantity', 1)

        try:
            qty = int(qty)
            if qty < 1:
                qty = 1
        except ValueError:
            qty = 1

        # Get product from DATABASE
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)

        cart_key = str(product_id)
        cart = request.session.get('cart', {})
        cart[cart_key] = cart.get(cart_key, 0) + qty
        request.session['cart'] = cart
        request.session.modified = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart': cart,
                'message': f'Added {qty}x {product.name} to cart!',
                'product_name': product.name,
                'price': float(product.price),
            })

        return redirect('cart_view')

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def cart_view(request):
    """Handle both database and static products in cart"""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for cart_key, quantity in cart.items():
        # Handle cart keys (simple product_id or product_id-thickness)
        if '-' in cart_key:
            product_id_str, thickness = cart_key.split('-', 1)
        else:
            product_id_str = cart_key
            thickness = None

        # Try database first
        product = None
        try:
            product = Product.objects.get(id=product_id_str, is_active=True)
            product_name = product.name
            product_price = float(product.price)
            product_image = product.image if hasattr(product, 'image') else None
        except Product.DoesNotExist:
            # FALLBACK: Look in products_data.py
            product_found = None
            for slug, product_data in products.items():
                if str(product_data.get('id', slug)) == str(product_id_str):
                    product_found = product_data
                    break
                # Check variants
                if 'variants' in product_data:
                    for variant in product_data['variants']:
                        if str(variant.get('id')) == str(product_id_str):
                            product_found = variant
                            break
                    if product_found:
                        break

            if not product_found:
                continue  # Skip invalid products

            product_name = product_found.get('name', 'Unknown Product')
            product_price = float(product_found.get('price', 0))
            product_image = None

        # Create display name with thickness if applicable
        display_name = product_name
        if thickness:
            display_name = f"{product_name} - {thickness}"

        subtotal = product_price * quantity
        cart_items.append({
            'product': {
                'id': product_id_str,
                'name': display_name,
                'price': product_price,
                'image': product_image,
            },
            'quantity': quantity,
            'subtotal': subtotal,
            'cart_key': cart_key,
        })
        total_price += subtotal

    # Calculate delivery cost based on steel detection
    is_steel_order = determine_if_steel_order(cart)

    if is_steel_order:
        delivery_cost = 68.18  # Steel products use old pricing
    else:
        delivery_cost = 143.50  # Non-steel products use new Zone 1 pricing

    gst = (total_price + delivery_cost) * 0.1
    grand_total = total_price + delivery_cost + gst

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'delivery_cost': delivery_cost,
        'gst': gst,
        'grand_total': grand_total,
    })


def update_cart(request):
    """Update cart quantities"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        # Update quantities from POST
        for key in request.POST:
            if key.startswith('quantity_'):
                try:
                    cart_key = key.split('quantity_', 1)[1]
                    quantity = int(request.POST[key])
                    if quantity > 0:
                        cart[cart_key] = quantity
                    else:
                        cart.pop(cart_key, None)
                except (ValueError, IndexError):
                    continue

        request.session['cart'] = cart
        request.session.modified = True

        # Calculate updated totals
        updated_items = []
        total_price = 0

        for cart_key, quantity in cart.items():
            if '-' in cart_key:
                product_id_str, thickness = cart_key.split('-', 1)
            else:
                product_id_str = cart_key
                thickness = None

            # Try database first, then static data
            try:
                product = Product.objects.get(id=product_id_str, is_active=True)
                price = float(product.price)
            except Product.DoesNotExist:
                # Look in static data
                product_found = None
                for slug, product_data in products.items():
                    if str(product_data.get('id', slug)) == str(product_id_str):
                        product_found = product_data
                        break
                    if 'variants' in product_data:
                        for variant in product_data['variants']:
                            if str(variant.get('id')) == str(product_id_str):
                                product_found = variant
                                break
                        if product_found:
                            break

                if not product_found:
                    continue

                price = float(product_found.get('price', 0))

            subtotal = price * quantity
            total_price += subtotal

            updated_items.append({
                'product_id': cart_key,
                'subtotal': subtotal,
            })

        return JsonResponse({
            'success': True,
            'items': updated_items,
            'total_price': total_price,
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def remove_from_cart(request, product_id):
    """Remove product from cart"""
    cart = request.session.get('cart', {})

    # Handle both simple product_id and thickness-specific keys
    keys_to_remove = []
    for cart_key in cart.keys():
        if cart_key == str(product_id) or cart_key.startswith(f"{product_id}-"):
            keys_to_remove.append(cart_key)

    for key in keys_to_remove:
        del cart[key]

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_view')


# ============================================================================
# DELIVERY AND PRICING
# ============================================================================

@require_POST
def calculate_delivery(request):
    """AJAX endpoint to calculate delivery cost based on postcode"""
    postcode = request.POST.get('postcode', '').strip()
    is_steel = request.POST.get('is_steel', 'false').lower() == 'true'

    if not postcode:
        return JsonResponse({'error': 'Postcode required'}, status=400)

    try:
        if is_steel:
            # Steel products - use OLD pricing system
            excel_path = os.path.join(settings.BASE_DIR, 'SA Postcode Zone List - Latif.xlsx')
            df = pd.read_excel(excel_path)

            row = df.loc[df['Postcode'].astype(str) == str(postcode)].iloc[0]
            zone = row['Zone'].strip().lower()

            if zone == 'metro':
                delivery_cost = Decimal('68.18')
                zone_display = 'Metro'
            elif zone == 'outer metro':
                delivery_cost = Decimal('81.80')
                zone_display = 'Outer Metro'
            else:
                delivery_cost = Decimal('150.00')
                zone_display = 'Regional'

            return JsonResponse({
                'success': True,
                'delivery_cost': delivery_cost,
                'zone': zone_display,
                'is_poa': False
            })
        else:
            # Non-steel products - use NEW zone pricing
            excel_path = os.path.join(settings.BASE_DIR, 'SA_by_zones.xlsx')
            df = pd.read_excel(excel_path)

            row = df.loc[df['Postcode'].astype(str) == str(postcode)].iloc[0]
            zone = str(row['Zones']).strip()

            pricing = {
                '1': Decimal('143.50'),
                '2': Decimal('181.50'),
                '3': Decimal('242.00'),
                '4': Decimal('302.50'),
                '5': Decimal('0.00')  # POA
            }

            delivery_cost = pricing.get(zone, Decimal('0.00'))
            zone_display = f'Zone {zone}'

            return JsonResponse({
                'success': True,
                'delivery_cost': delivery_cost,
                'zone': zone_display,
                'is_poa': zone == '5'
            })

    except Exception as e:
        print(f"❌ Calculate delivery error: {str(e)}")
        return JsonResponse({
            'success': True,
            'delivery_cost': 150.00,  # Default
            'zone': 'Regional',
            'is_poa': False
        })


@require_POST
def check_cart_steel(request):
    """AJAX endpoint to check if cart contains steel products"""
    try:
        cart = request.session.get('cart', {})
        is_steel_order = determine_if_steel_order(cart)

        return JsonResponse({
            'success': True,
            'is_steel_order': is_steel_order
        })
    except Exception as e:
        print(f"❌ Error checking cart steel: {str(e)}")
        return JsonResponse({
            'success': False,
            'is_steel_order': False
        })


# ============================================================================
# CHECKOUT AND PAYMENT
# ============================================================================

# Set stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout_view(request):
    """Display checkout form with discount support"""
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_view')

    # Determine if steel order for proper delivery calculation
    is_steel_order = determine_if_steel_order(cart)

    # Calculate cart totals using DATABASE products
    cart_items = []
    subtotal = Decimal('0.00')

    for cart_key, quantity in cart.items():
        if '-' in cart_key:
            product_id_str, thickness = cart_key.split('-', 1)
        else:
            product_id_str = cart_key
            thickness = None

        try:
            product = Product.objects.get(id=product_id_str, is_active=True)
        except Product.DoesNotExist:
            continue

        price = Decimal(str(product.price))
        quantity_decimal = Decimal(str(quantity))

        if thickness:
            display_name = f"{product.name} - {thickness}"
        else:
            display_name = product.name

        item_total = price * quantity_decimal
        cart_items.append({
            'cart_key': cart_key,
            'name': display_name,
            'price': price,
            'quantity': quantity,
            'total': item_total,
            'product': product
        })
        subtotal += item_total

    # Get applied discount from session
    applied_discount = request.session.get('applied_discount')
    discount_amount = Decimal('0.00')

    # Set delivery cost based on steel order detection
    if is_steel_order:
        delivery_cost = Decimal('68.18')  # Default steel pricing (Metro)
    else:
        delivery_cost = Decimal('143.50')  # Default Zone 1 pricing for non-steel

    if applied_discount:
        discount_amount = Decimal(str(applied_discount['discount_amount']))
        if applied_discount.get('discount_type') == 'free_shipping':
            delivery_cost = Decimal('0.00')

    # Calculate totals
    if applied_discount and applied_discount.get('discount_type') != 'free_shipping':
        discounted_subtotal = subtotal - discount_amount
    else:
        discounted_subtotal = subtotal

    gst = (discounted_subtotal + delivery_cost) * Decimal('0.10')
    total = discounted_subtotal + delivery_cost + gst

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'applied_discount': applied_discount,
        'discount_amount': discount_amount,
        'delivery_cost': delivery_cost,
        'gst': gst,
        'total': total,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'google_maps_api_key': getattr(settings, 'AIzaSyCuo9o_t0Uwcjt7ZwogeoJ9etxI4nzTfbs', ''),
    }

    return render(request, 'checkout.html', context)


@require_POST
def create_payment_intent(request):
    """Create Stripe payment intent"""
    try:
        data = json.loads(request.body)

        # Get cart and calculate total
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # Calculate totals using DATABASE products
        subtotal = Decimal('0.00')

        for cart_key, quantity in cart.items():
            if '-' in cart_key:
                product_id_str, thickness = cart_key.split('-', 1)
            else:
                product_id_str = cart_key
                thickness = None

            try:
                product = Product.objects.get(id=product_id_str, is_active=True)
            except Product.DoesNotExist:
                continue

            price = Decimal(str(product.price))
            subtotal += price * Decimal(str(quantity))

        # Get applied discount from session
        applied_discount = request.session.get('applied_discount')
        discount_amount = Decimal('0.00')

        if applied_discount:
            discount_amount = Decimal(str(applied_discount['discount_amount']))

        # Calculate delivery cost
        delivery_cost = Decimal(str(data.get('delivery_cost', '68.18')))

        # Apply free shipping discount if applicable
        if applied_discount and applied_discount.get('discount_type') == 'free_shipping':
            delivery_cost = Decimal('0.00')

        # Calculate final totals
        if applied_discount and applied_discount.get('discount_type') != 'free_shipping':
            discounted_subtotal = subtotal - discount_amount
        else:
            discounted_subtotal = subtotal

        gst = (discounted_subtotal + delivery_cost) * Decimal('0.10')
        total = discounted_subtotal + delivery_cost + gst

        # Convert to cents for Stripe
        amount_cents = int(total * 100)

        # Validate amount
        if amount_cents < 50:  # Stripe minimum is $0.50 AUD
            return JsonResponse({'error': 'Order total too small'}, status=400)

        # Create payment intent
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='aud',
                metadata={
                    'customer_email': data.get('email', ''),
                    'customer_name': f"{data.get('first_name', '')} {data.get('last_name', '')}",
                    'delivery_postcode': data.get('delivery_postcode', ''),
                    'subtotal': str(subtotal),
                    'delivery_cost': str(delivery_cost),
                    'discount_amount': str(discount_amount),
                    'gst': str(gst),
                    'total': str(total),
                }
            )
        except stripe.error.StripeError as e:
            print(f"❌ Stripe error: {str(e)}")
            return JsonResponse({'error': f'Payment processing error: {str(e)}'}, status=400)

        return JsonResponse({
            'client_secret': intent.client_secret,
            'amount': float(total)
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"❌ Payment intent error: {str(e)}")
        return JsonResponse({'error': f'Internal error: {str(e)}'}, status=500)


@require_POST
def process_order(request):
    """Process the order after successful payment - FIXED DISCOUNT HANDLING"""
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return JsonResponse({'error': 'Payment intent ID required'}, status=400)

        # Verify payment with Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status != 'succeeded':
                return JsonResponse({'error': 'Payment not completed'}, status=400)
        except Exception as e:
            print(f"❌ Stripe verification error: {str(e)}")
            return JsonResponse({'error': 'Invalid payment'}, status=400)

        # Get or create customer
        customer_data = {
            'email': data['email'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data.get('phone', ''),
            'billing_address_line1': data.get('billing_address_line1', ''),
            'billing_city': data.get('billing_city', ''),
            'billing_state': data.get('billing_state', ''),
            'billing_postcode': data.get('billing_postcode', ''),
            'delivery_address_line1': data.get('delivery_address_line1', ''),
            'delivery_city': data.get('delivery_city', ''),
            'delivery_state': data.get('delivery_state', ''),
            'delivery_postcode': data.get('delivery_postcode', ''),
        }

        customer, created = Customer.objects.get_or_create(
            email=customer_data['email'],
            defaults=customer_data
        )

        if not created:
            for key, value in customer_data.items():
                setattr(customer, key, value)
            customer.save()

        cart = request.session.get('cart', {})
        is_steel_order = determine_if_steel_order(cart)

        customer.calculate_delivery_cost()

        # Get delivery slot info
        delivery_slot_id = data.get('delivery_slot_id')
        delivery_slot = None
        if delivery_slot_id:
            try:
                delivery_slot = DeliverySlot.objects.get(id=delivery_slot_id)
                delivery_date = delivery_slot.date
                delivery_time_slot = delivery_slot.time_slot
            except DeliverySlot.DoesNotExist:
                delivery_date = None
                delivery_time_slot = None
        else:
            delivery_date = None
            delivery_time_slot = None

        # Get applied discount - FIXED
        applied_discount = request.session.get('applied_discount')

        # Get discount object if applied
        discount_code_obj = None
        discount_amount = Decimal('0.00')
        if applied_discount:
            try:
                discount_code_obj = DiscountCode.objects.get(id=applied_discount['discount_id'])
                discount_amount = Decimal(str(applied_discount['discount_amount']))
            except DiscountCode.DoesNotExist:
                print(f"⚠️ Discount code {applied_discount.get('discount_id')} not found")
                pass

        # Calculate delivery cost
        base_delivery_cost = customer.delivery_cost
        final_delivery_cost = base_delivery_cost
        if applied_discount and applied_discount.get('discount_type') == 'free_shipping':
            final_delivery_cost = Decimal('0.00')

        # Create order with discount info
        order = Order.objects.create(
            customer=customer,
            subtotal=Decimal('0.00'),  # Will be calculated
            delivery_cost=final_delivery_cost,
            tax_amount=Decimal('0.00'),  # Will be calculated
            total_amount=Decimal('1.00'),  # Temporary
            stripe_payment_intent_id=payment_intent_id,
            paid_at=timezone.now(),
            status='processing',
            delivery_slot=delivery_slot,
            delivery_date=delivery_date,
            special_requests=data.get('special_requests', ''),
            delivery_time_slot=delivery_time_slot,
            discount_code=discount_code_obj,
            discount_amount=discount_amount,
            discount_type=applied_discount.get('discount_type', '') if applied_discount else '',
        )

        # Create order items using DATABASE products - FIXED
        subtotal = Decimal('0.00')
        for cart_key, quantity in cart.items():
            if '-' in cart_key:
                product_id_str, thickness = cart_key.split('-', 1)
            else:
                product_id_str = cart_key
                thickness = None

            try:
                # FIXED: Use database Product model directly
                product = Product.objects.get(id=product_id_str, is_active=True)
            except Product.DoesNotExist:
                print(f"⚠️ Skipping product {product_id_str} - not found in database")
                continue

            unit_price = Decimal(str(product.price))
            quantity_decimal = Decimal(str(quantity))
            product_name = product.name

            # Add thickness to product name if applicable
            if thickness:
                product_name = f"{product.name} - {thickness}"

            # Create order item
            OrderItem.objects.create(
                order=order,
                product_id=str(product.id),  # FIXED: Use database ID
                product_name=product_name,
                product_length=getattr(product, 'length', ''),
                product_thickness=thickness or '',
                unit_price=unit_price,
                quantity=quantity
            )

            subtotal += unit_price * quantity_decimal

        # Update order totals now that we have all items
        order.calculate_totals()

        # Record discount usage if applied - FIXED
        if discount_code_obj and discount_amount > 0:
            DiscountUsage.objects.create(
                discount_code=discount_code_obj,
                order=order,
                customer_email=customer.email,
                discount_amount=discount_amount
            )
            print(f"✅ Recorded discount usage: {discount_code_obj.code} - ${discount_amount}")

        # Clear cart and discount from session
        request.session['cart'] = {}
        if 'applied_discount' in request.session:
            del request.session['applied_discount']
        request.session.modified = True

        # Send confirmation email
        try:
            send_order_confirmation_email(order)
        except Exception as e:
            print(f"❌ Email sending failed: {str(e)}")

        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'redirect_url': f'/order-confirmation/{order.order_number}/'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"❌ Order processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Order processing failed: {str(e)}'}, status=500)


# DEBUGGING FUNCTION: Test discount calculation
def debug_discount_calculation(request):
    """Debug endpoint to test discount calculations"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        # Get a sample cart
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'error': 'Cart is empty'})

        # Get all active discount codes
        discounts = DiscountCode.objects.filter(is_active=True)

        # Calculate cart items
        cart_items = []
        subtotal = Decimal('0.00')

        for cart_key, quantity in cart.items():
            if '-' in cart_key:
                product_id_str, thickness = cart_key.split('-', 1)
            else:
                product_id_str = cart_key
                thickness = None

            try:
                product = Product.objects.get(id=product_id_str, is_active=True)
                price = Decimal(str(product.price))
                quantity_decimal = Decimal(str(quantity))
                item_total = price * quantity_decimal

                cart_items.append({
                    'cart_key': cart_key,
                    'product_id': str(product.id),
                    'name': product.name,
                    'category': product.category,
                    'price': price,
                    'quantity': quantity,
                    'total': item_total,
                })
                subtotal += item_total

            except Product.DoesNotExist:
                continue

        # Test each discount
        results = []
        delivery_cost = Decimal('68.18')

        for discount in discounts:
            discount_amount = discount.calculate_discount(cart_items, subtotal, delivery_cost)

            results.append({
                'code': discount.code,
                'name': discount.name,
                'type': discount.discount_type,
                'value': float(discount.discount_value),
                'calculated_discount': float(discount_amount),
                'applicable_products': discount.applicable_products.count(),
                'exclude_products': discount.exclude_products.count(),
                'applicable_categories': discount.applicable_categories,
                'exclude_categories': discount.exclude_categories,
            })

        return JsonResponse({
            'success': True,
            'cart_subtotal': float(subtotal),
            'cart_items': len(cart_items),
            'discount_tests': results,
            'sample_items': [
                {
                    'name': item['name'],
                    'category': item['category'],
                    'total': float(item['total'])
                } for item in cart_items[:3]
            ]
        })

    except Exception as e:
        print(f"❌ Debug discount error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def order_confirmation(request, order_number):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'order_confirmation.html', {'order': order})


def send_order_confirmation_email(order):
    """Send order confirmation email with beautiful template"""
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives

    subject = f'Order Confirmation - {order.order_number} | Wall Quote'

    # Render HTML email
    html_content = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'customer': order.customer
    })

    # Simple text version
    text_content = f"""
    Thank you for your order!

    Order Number: {order.order_number}
    Total: ${order.total_amount}
    Status: {order.get_status_display()}

    We'll contact you within 24 hours to arrange delivery.

    Thank you for choosing Wall Quote!
    """

    # Send email with both HTML and text versions
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


# ============================================================================
# DISCOUNT MANAGEMENT
# ============================================================================

@require_POST
def apply_discount(request):
    """Apply discount code to current cart - FIXED TO USE DATABASE PRODUCTS"""
    try:
        data = json.loads(request.body)
        discount_code = data.get('code', '').strip().upper()

        if not discount_code:
            return JsonResponse({'success': False, 'error': 'Please enter a discount code'})

        # Get cart
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'success': False, 'error': 'Your cart is empty'})

        # Find discount code
        try:
            discount = DiscountCode.objects.get(code=discount_code)
        except DiscountCode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid discount code'})

        # Check if discount is valid
        if not discount.is_valid_now:
            if not discount.is_active:
                return JsonResponse({'success': False, 'error': 'This discount code is no longer active'})
            elif discount.valid_until and timezone.now() > discount.valid_until:
                return JsonResponse({'success': False, 'error': 'This discount code has expired'})
            elif discount.valid_from and timezone.now() < discount.valid_from:
                return JsonResponse({'success': False, 'error': 'This discount code is not yet valid'})
            else:
                return JsonResponse({'success': False, 'error': 'This discount code has reached its usage limit'})

        # Check customer usage
        customer_email = data.get('email', request.session.get('customer_email', ''))
        if customer_email and not discount.can_be_used_by_customer(customer_email):
            return JsonResponse({'success': False, 'error': 'You have already used this discount code'})

        # Calculate cart totals using DATABASE products - FIXED
        cart_items = []
        subtotal = Decimal('0.00')

        for cart_key, quantity in cart.items():
            if '-' in cart_key:
                product_id_str, thickness = cart_key.split('-', 1)
            else:
                product_id_str = cart_key
                thickness = None

            try:
                # FIXED: Use database Product model directly
                product = Product.objects.get(id=product_id_str, is_active=True)
                price = Decimal(str(product.price))
                quantity_decimal = Decimal(str(quantity))
                item_total = price * quantity_decimal

                cart_items.append({
                    'cart_key': cart_key,
                    'product_id': str(product.id),  # FIXED: Use database ID
                    'name': product.name,
                    'price': price,
                    'quantity': quantity,
                    'total': item_total,
                    'product': product,  # ADDED: Include full product object
                })
                subtotal += item_total

            except Product.DoesNotExist:
                print(f"⚠️ Product {product_id_str} not found in database")
                continue

        if not cart_items:
            return JsonResponse({'success': False, 'error': 'No valid products found in cart'})

        # Check minimum order amount
        if discount.minimum_order_amount and subtotal < discount.minimum_order_amount:
            return JsonResponse({
                'success': False,
                'error': f'Minimum order amount of ${discount.minimum_order_amount} required for this discount'
            })

        # Calculate delivery cost
        delivery_cost = Decimal(str(data.get('delivery_cost', '68.18')))

        # Calculate discount amount using FIXED method
        discount_amount = discount.calculate_discount(cart_items, subtotal, delivery_cost)

        if discount_amount <= 0:
            return JsonResponse({'success': False, 'error': 'This discount is not applicable to items in your cart'})

        # Store discount in session
        request.session['applied_discount'] = {
            'code': discount.code,
            'discount_id': discount.id,
            'discount_amount': float(discount_amount),
            'discount_type': discount.discount_type,
            'description': discount.description,
        }
        request.session.modified = True

        # Calculate new totals
        if discount.discount_type == 'free_shipping':
            new_delivery_cost = Decimal('0.00')
            new_subtotal = subtotal
        else:
            new_delivery_cost = delivery_cost
            new_subtotal = subtotal - discount_amount

        new_gst = (new_subtotal + new_delivery_cost) * Decimal('0.10')
        new_total = new_subtotal + new_delivery_cost + new_gst

        return JsonResponse({
            'success': True,
            'discount': {
                'code': discount.code,
                'description': discount.description,
                'amount': float(discount_amount),
                'type': discount.discount_type,
            },
            'totals': {
                'subtotal': float(subtotal),
                'discount_amount': float(discount_amount),
                'delivery_cost': float(new_delivery_cost),
                'gst': float(new_gst),
                'total': float(new_total),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request data'})
    except Exception as e:
        print(f"❌ Apply discount error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'Internal server error'})


@require_POST
def remove_discount(request):
    """Remove applied discount from cart"""
    if 'applied_discount' in request.session:
        del request.session['applied_discount']
        request.session.modified = True

    return JsonResponse({'success': True, 'message': 'Discount removed'})


# ============================================================================
# DELIVERY SLOTS
# ============================================================================

def get_delivery_slots(request):
    """Get available delivery slots for the next 7 days"""
    from datetime import date, timedelta
    import logging

    logger = logging.getLogger(__name__)

    try:
        slot_type = request.GET.get('type', 'delivery')
        logger.info(f"🔍 get_delivery_slots called with type: {slot_type}")

        # Only show next 7 days
        start_date = date.today() + timedelta(days=1)  # Start from tomorrow
        end_date = start_date + timedelta(days=7)  # Only 1 week ahead

        logger.info(f"🔍 Looking for slots between {start_date} and {end_date}")

        # Auto-generate slots if needed
        from django.core.management import call_command
        from io import StringIO

        try:
            out = StringIO()
            call_command('generate_delivery_slots', days=7, stdout=out)
            logger.info(f"🔄 Auto-generated slots for upcoming week")
        except Exception as e:
            logger.warning(f"⚠️ Could not auto-generate slots: {str(e)}")

        # Filter slots based on type
        if slot_type == 'pickup':
            slots = DeliverySlot.objects.filter(
                date__range=[start_date, end_date],
                is_available=True,
                delivery_type__in=['pickup', 'Both Available']
            ).order_by('date', 'time_slot')
        else:
            slots = DeliverySlot.objects.filter(
                date__range=[start_date, end_date],
                is_available=True,
                delivery_type__in=['internal', 'external', 'Both Available']
            ).order_by('date', 'time_slot')

        logger.info(f"🔍 Found {slots.count()} {slot_type} slots")

        # Only show slots with available capacity
        available_slots = []
        for slot in slots:
            if slot.available_capacity > 0:
                available_slots.append(slot)

        logger.info(f"🔍 {len(available_slots)} slots have available capacity")

        slots_data = []
        for slot in available_slots:
            slot_data = {
                'id': slot.id,
                'date': slot.date.isoformat(),
                'time_slot': slot.time_slot,
                'available_capacity': slot.available_capacity,
                'delivery_type': slot.delivery_type,
                'capacity': slot.capacity,
                'orders_count': slot.orders_count,
                'is_auto_generated': slot.is_auto_generated,
                'template_name': slot.template.name if slot.template else None,
            }
            slots_data.append(slot_data)
            logger.debug(f"📅 Slot: {slot.date} {slot.time_slot} - {slot.available_capacity} available")

        return JsonResponse({
            'success': True,
            'slots': slots_data,
            'total_found': len(slots_data),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })

    except Exception as e:
        logger.error(f"❌ Error in get_delivery_slots: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Failed to load delivery slots',
            'message': str(e)
        }, status=500)


# ============================================================================
# LEGACY AND UTILITY FUNCTIONS
# ============================================================================

def faq_view(request):
    """FAQ page"""
    faqs = FAQ.objects.all().order_by('order')
    return render(request, 'faq.html', {'faqs': faqs})


def blog_list(request):
    """Blog listing page"""
    posts = BlogPost.objects.filter(published=True).order_by('-created_at')
    return render(request, 'blog_list.html', {'posts': posts})


def blog_detail(request, slug):
    """Blog detail page"""
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog_detail.html', {'post': post})


def product_detail(request, slug):
    """Product detail view"""
    print(f"🔍 Looking for product with slug: '{slug}'")
    print(f"🔍 Available product keys: {list(products.keys())}")

    # Get the product from products_data.py
    product = products.get(slug)

    if not product:
        print(f"❌ Product '{slug}' not found in products dictionary")
        similar = [key for key in products.keys() if slug.lower() in key.lower()]
        if similar:
            print(f"🔍 Similar products found: {similar}")

        return render(request, 'product_detail.html', {
            'product': None,
            'product_name': slug,
            'slug': slug,
            'error_message': f"Product '{slug}' not found. Available products: {list(products.keys())}"
        })

    print(f"✅ Product found: {product.get('name', 'No name')}")

    context = {
        'product': product,
        'product_id': product.get('id', 0),
        'product_name': product.get('name', 'Unknown Product'),
        'slug': slug,
    }

    return render(request, 'product_detail.html', context)


def test_email(request):
    """Test email sending"""
    try:
        send_mail(
            subject='Test Email from Wall Quote System',
            message='This is a test email to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['adamib123456789@gmail.com'],
            fail_silently=False,
        )
        return HttpResponse("Email sent successfully!")
    except Exception as e:
        return HttpResponse(f"Email failed: {str(e)}")


def health_check(request):
    """Simple health check endpoint"""
    try:
        # Test database connection
        Product.objects.count()

        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


# ============================================================================
# HELPER FUNCTIONS FOR CONVERSIONS
# ============================================================================

def convert_length_to_mm(length_str):
    """Convert '2.0m' to '2000', '2.34m' to '2340'"""
    if not length_str:
        return ''

    try:
        # Remove 'm' and convert to float, then to mm
        meters = float(length_str.replace('m', ''))
        mm = int(meters * 1000)
        return str(mm)
    except:
        return ''


def convert_dimension_to_mm(dimension_str):
    """Convert '200mm' to '200', '100mm' to '100'"""
    if not dimension_str:
        return ''

    try:
        # Extract number from strings like '200mm', '200 tapered to 100mm'
        import re
        match = re.search(r'(\d+)', dimension_str)
        if match:
            return match.group(1)
        return ''
    except:
        return ''


# ============================================================================
# ESSENTIAL MISSING FUNCTIONS (restored for compatibility)
# ============================================================================

@require_GET
def get_products_ajax(request):
    """AJAX endpoint to get filtered products - RESTORED"""
    try:
        category = request.GET.get('category', '')
        subcategory = request.GET.get('subcategory', '')
        brand = request.GET.get('brand', '')
        search = request.GET.get('search', '')

        print(f"🔍 AJAX Filter request: category={category}, subcategory={subcategory}, search={search}")

        # Start with all active products
        products = Product.objects.filter(is_active=True)
        print(f"🔍 Total active products: {products.count()}")

        # Apply category filter
        if category and category != 'all':
            products = ProductGroupManager.apply_category_filter(products, category)
            print(f"🔍 After category filter: {products.count()}")

        # Apply search filter
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(category__icontains=search)
            )
            print(f"🔍 After search filter: {products.count()}")

        # Group products to avoid showing duplicates
        product_groups = ProductGroupManager.group_products_efficiently(products)

        # Apply subcategory filtering
        filtered_groups = {}
        for group_key, group_data in product_groups.items():
            include_group = True

            # Apply subcategory filtering
            if subcategory and subcategory.strip():
                filter_subcategory = subcategory.lower().replace('-', ' ').strip()
                product_subcategory = group_data['subcategory'].lower().strip()

                if filter_subcategory not in product_subcategory and product_subcategory not in filter_subcategory:
                    include_group = False

            if include_group:
                filtered_groups[group_key] = group_data

        # Convert groups to organized products
        organized_products = []
        for group_key, group_data in filtered_groups.items():
            representative = group_data['representative_product']

            # Handle image field properly for JSON serialization
            image_url = None
            if hasattr(representative, 'image') and representative.image:
                try:
                    image_url = representative.image.url
                except (ValueError, AttributeError):
                    image_url = None

            product_data = {
                'id': representative.id,
                'name': representative.name,
                'price': float(representative.price),
                'category': group_data['main_category'],
                'subcategory': group_data['subcategory'],
                'brand': group_data['brand'] or "",
                'image': image_url,
                'sku': getattr(representative, 'sku', ''),
                'category_slug': group_data['main_category'].lower().replace(' ', '-'),
                'subcategory_slug': group_data['subcategory'].lower().replace(' ', '-').replace('/', '-'),
                'brand_slug': (group_data['brand'] or "").lower().replace(' ', '-'),
                'variant_count': group_data['variant_count']
            }
            organized_products.append(product_data)

        print(f"🔍 Returning {len(organized_products)} organized product groups")

        return JsonResponse({
            'success': True,
            'products': organized_products,
            'count': len(organized_products)
        })

    except Exception as e:
        print(f"❌ Error in get_products_ajax: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'products': [],
            'count': 0
        }, status=500)


@require_GET
def get_product_variants_ajax(request, product_id):
    """Get available size variants for a product - RESTORED"""
    try:
        # Get the base product
        base_product = Product.objects.get(id=product_id, is_active=True)
        main_category = ProductGroupManager.get_main_category(base_product.category)

        # Determine the product group
        if main_category == "Concrete Sleepers":
            color_group = ProductGroupManager.determine_sleeper_color_exact(base_product)
            brand = ProductGroupManager.extract_brand_from_product(base_product)
        elif main_category == "Under Fence Plinths":
            color_group = ProductGroupManager.determine_ufp_color_exact(base_product)
            brand = ProductGroupManager.extract_brand_from_product(base_product)
        elif main_category == "Galvanised Steel":
            steel_type = ProductGroupManager.determine_steel_product_exact(base_product)
            brand = None
        else:
            # No variants for other types
            return JsonResponse({
                'success': True,
                'variants': [],
                'has_variants': False
            })

        # Find all products with the same color/type and brand
        all_products = Product.objects.filter(is_active=True)
        variants = []

        for product in all_products:
            product_main_category = ProductGroupManager.get_main_category(product.category)

            # Check if this product belongs to the same group
            if product_main_category == main_category:
                should_include = False

                if main_category == "Concrete Sleepers":
                    product_color = ProductGroupManager.determine_sleeper_color_exact(product)
                    product_brand = ProductGroupManager.extract_brand_from_product(product)
                    if product_color == color_group and product_brand == brand:
                        should_include = True

                elif main_category == "Under Fence Plinths":
                    product_color = ProductGroupManager.determine_ufp_color_exact(product)
                    product_brand = ProductGroupManager.extract_brand_from_product(product)
                    if product_color == color_group and product_brand == brand:
                        should_include = True

                elif main_category == "Galvanised Steel":
                    product_steel_type = ProductGroupManager.determine_steel_product_exact(product)
                    if product_steel_type == steel_type:
                        should_include = True

                if should_include:
                    # Extract size information
                    details = ProductGroupManager.extract_product_details_for_filtering(product)

                    if main_category == "Galvanised Steel":
                        size_info = details.get('length', 'Unknown length')
                    else:
                        length = details.get('length', 'Unknown')
                        height = details.get('height', 'Unknown')
                        thickness = details.get('thickness', 'Unknown')
                        size_info = f"{length} × {height} × {thickness}"

                    variants.append({
                        'id': product.id,
                        'name': product.name,
                        'price': float(product.price),
                        'size_display': size_info,
                        'length': details.get('length', ''),
                        'height': details.get('height', ''),
                        'thickness': details.get('thickness', ''),
                    })

        # Sort variants by price
        variants.sort(key=lambda x: x['price'])

        # Only show dropdown if there are multiple variants
        has_variants = len(variants) > 1

        return JsonResponse({
            'success': True,
            'variants': variants,
            'has_variants': has_variants,
            'base_product': {
                'id': base_product.id,
                'name': base_product.name,
                'price': float(base_product.price)
            }
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        print(f"❌ Error getting variants: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# LEGACY VARIANT FUNCTIONS (kept for compatibility)
# ============================================================================

def add_to_cart_variant(request, variant_id):
    """Add product variant to cart using new structure"""
    if request.method == "POST":
        qty = request.POST.get('quantity', 1)

        try:
            qty = int(qty)
            if qty < 1:
                qty = 1
        except ValueError:
            qty = 1

        # Get variant from new ProductVariant model
        try:
            variant = ProductVariant.objects.get(id=variant_id, is_active=True)
        except ProductVariant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)

        # Use variant ID as cart key
        cart_key = f"variant_{variant_id}"

        cart = request.session.get('cart', {})
        cart[cart_key] = cart.get(cart_key, 0) + qty
        request.session['cart'] = cart
        request.session.modified = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart': cart,
                'message': f'Added {qty}x {variant.name} to cart!',
                'product_name': variant.name,
                'price': float(variant.price_inc_gst),  # Show inc GST to customer
            })

        return redirect('cart_view')

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def get_product_variants(request, product_id):
    """Get variants for a specific product"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        variants = ProductVariant.objects.filter(product=product, is_active=True)

        variants_data = []
        for variant in variants:
            variants_data.append({
                'id': variant.id,
                'name': variant.name,
                'price': float(variant.price_ex_gst),
                'price_inc_gst': float(variant.price_inc_gst),
                'sku': variant.sku,
                'specifications': variant.specifications,
            })

        return JsonResponse({
            'success': True,
            'variants': variants_data
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, '404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    return render(request, '500.html', status=500)


# ============================================================================
# DEBUG FUNCTIONS (for development)
# ============================================================================

def debug_cart_contents(request):
    """Debug function to check what's in cart and if steel is detected"""
    cart = request.session.get('cart', {})

    print("🔍 CART DEBUG:")
    for cart_key, quantity in cart.items():
        if '-' in cart_key:
            product_id_str, thickness = cart_key.split('-', 1)
        else:
            product_id_str = cart_key

        try:
            product = Product.objects.get(id=product_id_str, is_active=True)
            is_steel = is_steel_product(product)
            print(f"   Product: {product.name}")
            print(f"   Category: {product.category}")
            print(f"   Is Steel: {is_steel}")
            print(f"   Quantity: {quantity}")
            print("   ---")
        except Product.DoesNotExist:
            print(f"   Product ID {product_id_str} not found")

    is_steel_order = determine_if_steel_order(cart)
    print(f"🚚 FINAL RESULT: Is steel order = {is_steel_order}")

    return JsonResponse({
        'is_steel_order': is_steel_order,
        'cart_items': len(cart)
    })


def debug_product_detail(request, slug):
    """Debug version of product detail"""
    return product_detail(request, slug)


def check_database_products(request):
    """Check what's actually in the database"""
    try:
        total = Product.objects.count()
        active = Product.objects.filter(is_active=True).count()
        inactive = Product.objects.filter(is_active=False).count()

        # Get category breakdown
        categories = {}
        for product in Product.objects.filter(is_active=True):
            cat = product.category
            if cat in categories:
                categories[cat] += 1
            else:
                categories[cat] = 1

        return JsonResponse({
            'total_products': total,
            'active_products': active,
            'inactive_products': inactive,
            'categories': categories
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})


# 2. Check what the ProductGroupManager is doing:
def debug_product_grouping(request):
    """Debug the product grouping logic"""
    try:
        products = Product.objects.filter(is_active=True)[:20]  # First 20 products

        # Test the grouping without the manager
        results = []
        for product in products:
            main_cat = ProductGroupManager.get_main_category(product.category)
            subcat = ProductGroupManager.determine_product_subcategory(product)
            brand = ProductGroupManager.extract_brand_from_product(product)

            results.append({
                'id': product.id,
                'name': product.name,
                'original_category': product.category,
                'main_category': main_cat,
                'subcategory': subcat,
                'brand': brand,
                'price': float(product.price)
            })

        # Now test the full grouping
        product_groups = ProductGroupManager.group_products_efficiently(products)

        return JsonResponse({
            'individual_products': results,
            'groups_created': len(product_groups),
            'group_keys': list(product_groups.keys())
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})


def our_range_debug(request):
    """Debug version to see what's going wrong"""
    try:
        # Get raw product count
        total_products = Product.objects.filter(is_active=True).count()
        print(f"🔍 Total active products in DB: {total_products}")

        # Get products without grouping
        products_qs = Product.objects.filter(is_active=True).order_by('category', 'name')
        print(f"🔍 Products after basic filter: {products_qs.count()}")

        # Test the grouping function
        product_groups = ProductGroupManager.group_products_efficiently(products_qs)
        print(f"🔍 Product groups created: {len(product_groups)}")

        # Show first few products for debugging
        sample_products = []
        for i, product in enumerate(products_qs[:10]):
            sample_products.append({
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'is_active': product.is_active,
                'price': float(product.price)
            })

        return JsonResponse({
            'total_in_db': total_products,
            'after_filter': products_qs.count(),
            'groups_created': len(product_groups),
            'sample_products': sample_products
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})


def debug_specific_group(request):
    """Debug a specific product group"""
    product_id = request.GET.get('product_id')

    if not product_id:
        return JsonResponse({'error': 'product_id required'})

    try:
        base_product = Product.objects.get(id=product_id, is_active=True)

        # Get all products and see how they group
        products = Product.objects.filter(is_active=True).order_by('name')
        product_groups = ProductGroupManager.group_products_efficiently(products)

        # Find which group this product belongs to
        target_group = None
        for group_key, group_data in product_groups.items():
            if any(p.id == int(product_id) for p in group_data['products']):
                target_group = {
                    'group_key': group_key,
                    'variant_count': group_data['variant_count'],
                    'representative_id': group_data['representative_product'].id,
                    'representative_name': group_data['representative_product'].name,
                    'all_products': [
                        {
                            'id': p.id,
                            'name': p.name,
                            'price': float(p.price)
                        } for p in group_data['products']
                    ]
                }
                break

        return JsonResponse({
            'base_product': {
                'id': base_product.id,
                'name': base_product.name,
                'category': base_product.category
            },
            'group_info': target_group
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})