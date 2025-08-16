from django.db import models
import os
import pandas as pd
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
import uuid
from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string


class QuoteRequest(models.Model):
    CALCULATOR_CHOICES = [
        ('retaining_wall', 'Retaining Wall'),
        ('under_fence_plinth', 'Under Fence Plinth'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('declined', 'Declined'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    delivery_address = models.CharField(max_length=255)
    delivery_postcode = models.CharField(max_length=10, null=True, blank=True)
    preferred_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phone = models.CharField(max_length=20)
    custom_message = models.TextField(blank=True, null=True, help_text="Additional notes or requirements from customer")

    calculator_type = models.CharField(max_length=30, choices=CALCULATOR_CHOICES)

    # retaining wall
    sleeper_length = models.FloatField(null=True, blank=True)
    sleeper_thickness = models.FloatField(null=True, blank=True)
    sleeper_style = models.CharField(max_length=100, null=True, blank=True)
    sleeper_brand = models.CharField(max_length=100, null=True, blank=True)
    wall_height = models.FloatField(null=True, blank=True)
    wall_length = models.FloatField(null=True, blank=True)
    total_sleepers = models.IntegerField(null=True, blank=True)
    steel_posts_required = models.IntegerField(null=True, blank=True)
    steel_post_height = models.FloatField(null=True, blank=True)
    steel_type = models.CharField(max_length=50, null=True, blank=True)

    # under fence plinth
    fence_length = models.FloatField(null=True, blank=True)
    plinths_per_panel = models.IntegerField(null=True, blank=True)
    total_panels = models.IntegerField(null=True, blank=True)
    total_plinths = models.IntegerField(null=True, blank=True)

    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # 🚚 Delivery fields
    delivery_zone = models.CharField(max_length=50, null=True, blank=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @property
    def total_cost(self):
        if self.estimated_cost and self.delivery_cost:
            return self.estimated_cost + self.delivery_cost
        return None

    def __str__(self):
        return f"{self.customer_name} - {self.get_calculator_type_display()} - {self.created_at.date()}"

    def save(self, *args, **kwargs):
        # Path to Excel file - FIXED: No quotes folder
        excel_path = os.path.join(settings.BASE_DIR, 'SA_by_zones.xlsx')

        # Read Excel
        df = pd.read_excel(excel_path)

        address = self.delivery_address.lower()
        zone = None

        for _, row in df.iterrows():
            postcode = str(row['Postcode']).strip()
            suburb = str(row['Suburb']).lower().strip()
            zone_number = str(row['Zones']).strip()

            if postcode in address or suburb in address:
                # Set zone based on new structure
                if zone_number == '1':
                    zone = 'zone1'
                    self.delivery_cost = 143.50
                elif zone_number == '2':
                    zone = 'zone2'
                    self.delivery_cost = 181.50
                elif zone_number == '3':
                    zone = 'zone3'
                    self.delivery_cost = 242.00
                elif zone_number == '4':
                    zone = 'zone4'
                    self.delivery_cost = 302.50
                elif zone_number == '5':
                    zone = 'zone5'
                    self.delivery_cost = 0.00  # POA

                self.delivery_zone = zone
                break

        if not zone:
            self.delivery_zone = 'unknown'
            self.delivery_cost = 0.00

        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # This should work for admin
    description = models.TextField(blank=True)

    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    category = models.CharField(max_length=100, default='General')
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    color = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    # Add this property to get the image URL safely
    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return '/static/images/no-image.png'  # Default image path

    # Add helper methods to extract specs from name
    def get_brand(self):
        """Extract brand from category"""
        if 'silvercrete' in self.category.lower():
            return 'silvercrete'
        elif 'outback' in self.category.lower():
            return 'outback'
        return None

    def get_color_finish(self):
        """Extract color/finish from name"""
        name_lower = self.name.lower()

        if '[grey]' in name_lower or 'grey' in name_lower:
            return 'plain-grey'
        elif '[sand]' in name_lower or 'sandstone' in name_lower:
            return 'plain-sandstone'
        elif '[char]' in name_lower or 'charcoal' in name_lower:
            if 'stackstone' in name_lower:
                return 'charcoal-stackstone'
            elif 'rockface' in name_lower:
                return 'charcoal-rockface'
            else:
                return 'plain-charcoal'
        elif 'rockface' in name_lower and 'sand' in name_lower:
            return 'sandstone-rockface'
        elif 'woodgrain' in name_lower:
            return 'woodgrain'

        return 'unknown'

    def extract_dimensions(self):
        """Extract length, height, thickness from product name"""
        import re

        # Common patterns in your product names
        # e.g., "SC Sleeper 2000x200x80 [GREY]"
        dimensions = {}

        # Extract dimensions like 2000x200x80
        dimension_match = re.search(r'(\d{3,4})x(\d{2,3})x(\d{2,3})', self.name)
        if dimension_match:
            length_mm = int(dimension_match.group(1))
            height_mm = int(dimension_match.group(2))
            thickness_mm = int(dimension_match.group(3))

            # Convert to display format
            dimensions['length'] = f"{length_mm / 1000:.1f}m" if length_mm >= 1000 else f"{length_mm}mm"
            dimensions['height'] = f"{height_mm}mm"
            dimensions['thickness'] = f"{thickness_mm}mm"

        # Handle special cases like "tapered"
        if 'tapered' in self.name.lower():
            dimensions['height'] = f"{dimensions.get('height', '200mm')} tapered to 100mm"

        return dimensions


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order in which this FAQ appears")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# =============================================
# DISCOUNT MODELS (DEFINED FIRST)
# =============================================

class DiscountCode(models.Model):
    """Discount codes that can be applied to orders"""

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed_amount', 'Fixed Amount Off'),
        ('free_shipping', 'Free Shipping'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Discount code (e.g. SAVE20, WELCOME10)")
    name = models.CharField(max_length=100, help_text="Internal name for this discount")
    description = models.TextField(blank=True, help_text="Description shown to customers")

    # Discount settings
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2,
                                         help_text="Percentage (e.g. 20 for 20%) or fixed amount")

    # Usage limits
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited uses")
    max_uses_per_customer = models.PositiveIntegerField(default=1,
                                                        help_text="How many times each customer can use this code")
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                               help_text="Minimum order total to use this code")

    # Date restrictions
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiry")

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Product restrictions - NOW DIRECT RELATIONSHIP TO Product MODEL
    applicable_products = models.ManyToManyField(
        'Product',  # Direct reference to Product model
        blank=True,
        help_text="Leave empty to apply to all products",
        related_name='applicable_discounts'
    )
    exclude_products = models.ManyToManyField(
        'Product',  # Direct reference to Product model
        blank=True,
        related_name='excluded_from_discounts',
        help_text="Products to exclude from this discount"
    )

    # OPTION: Category-based restrictions (more flexible)
    applicable_categories = models.TextField(
        blank=True,
        help_text="Comma-separated list of categories to include (e.g. 'Steel,Sleepers')"
    )
    exclude_categories = models.TextField(
        blank=True,
        help_text="Comma-separated list of categories to exclude"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def times_used(self):
        return DiscountUsage.objects.filter(discount_code=self).count()

    @property
    def is_valid_now(self):
        """Check if discount is currently valid (active and within date range)"""
        now = timezone.now()

        if not self.is_active:
            return False

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        if self.max_uses and self.times_used >= self.max_uses:
            return False

        return True

    def can_be_used_by_customer(self, customer_email):
        """Check if a specific customer can use this discount"""
        if not self.is_valid_now:
            return False

        customer_usage = DiscountUsage.objects.filter(
            discount_code=self,
            customer_email=customer_email
        ).count()

        return customer_usage < self.max_uses_per_customer

    def calculate_discount(self, cart_items, subtotal, delivery_cost=0):
        """Calculate discount amount for given cart items - FIXED TO USE DATABASE PRODUCTS"""
        applicable_total = Decimal('0.00')

        # Get applicable categories as list
        applicable_cats = [cat.strip() for cat in self.applicable_categories.split(',') if
                           cat.strip()] if self.applicable_categories else []
        exclude_cats = [cat.strip() for cat in self.exclude_categories.split(',') if
                        cat.strip()] if self.exclude_categories else []

        for item in cart_items:
            # Extract product ID from cart item
            product_id = item.get('product_id') or item.get('cart_key', '').split('-')[0]

            try:
                # Get the actual Product from database
                product = Product.objects.get(id=product_id, is_active=True)
                item_total = item.get('total', 0)

                # Check if this product should be included
                include_product = True

                # Check specific product inclusions
                if self.applicable_products.exists():
                    include_product = self.applicable_products.filter(id=product.id).exists()

                # Check specific product exclusions
                if include_product and self.exclude_products.exists():
                    include_product = not self.exclude_products.filter(id=product.id).exists()

                # Check category inclusions
                if include_product and applicable_cats:
                    include_product = any(cat.lower() in product.category.lower() for cat in applicable_cats)

                # Check category exclusions
                if include_product and exclude_cats:
                    include_product = not any(cat.lower() in product.category.lower() for cat in exclude_cats)

                if include_product:
                    applicable_total += Decimal(str(item_total))

            except Product.DoesNotExist:
                # Product not found in database, skip
                continue

        # If no specific restrictions, apply to all items
        if (not self.applicable_products.exists() and
                not self.exclude_products.exists() and
                not applicable_cats and
                not exclude_cats):
            applicable_total = Decimal(str(subtotal))

        # Calculate discount based on type
        if self.discount_type == 'percentage':
            discount_amount = applicable_total * (self.discount_value / 100)
        elif self.discount_type == 'fixed_amount':
            discount_amount = min(self.discount_value, applicable_total)
        elif self.discount_type == 'free_shipping':
            discount_amount = Decimal(str(delivery_cost))
        else:
            discount_amount = Decimal('0.00')

        return min(discount_amount, applicable_total + (
            Decimal(str(delivery_cost)) if self.discount_type == 'free_shipping' else Decimal('0.00')))


class DiscountableProduct(models.Model):
    """LEGACY - Keep for data migration purposes only"""

    product_id = models.CharField(max_length=50, unique=True, help_text="LEGACY: Product ID from products_data.py")
    name = models.CharField(max_length=200, help_text="Product name")
    category = models.CharField(max_length=100, blank=True, help_text="Product category")

    # Add mapping to new Product model
    mapped_product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Mapped to new Product model"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"LEGACY: {self.name} (ID: {self.product_id})"


class Customer(models.Model):
    """Customer information for orders"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Billing Address
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postcode = models.CharField(max_length=10, blank=True)
    billing_country = models.CharField(max_length=100, default='Australia')

    # Delivery Address
    delivery_address_line1 = models.CharField(max_length=255, blank=True)
    delivery_address_line2 = models.CharField(max_length=255, blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_state = models.CharField(max_length=100, blank=True)
    delivery_postcode = models.CharField(max_length=10, blank=True)
    delivery_country = models.CharField(max_length=100, default='Australia')

    # Delivery zone calculated from postcode
    delivery_zone = models.CharField(max_length=50, blank=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def calculate_delivery_cost(self, is_steel_order=False):
        """Calculate delivery cost based on postcode and product type"""
        if not self.delivery_postcode:
            return 0.00

        try:
            if is_steel_order:
                # Steel products keep the OLD pricing system
                excel_path = os.path.join(settings.BASE_DIR,
                                          'SA Postcode Zone List - Latif.xlsx')  # FIXED: No quotes folder
                df = pd.read_excel(excel_path)

                row = df.loc[df['Postcode'].astype(str) == str(self.delivery_postcode)].iloc[0]
                zone = row['Zone'].strip().lower()

                if zone == 'metro':
                    self.delivery_zone = 'Metro'
                    self.delivery_cost = Decimal('68.18')
                elif zone == 'outer metro':
                    self.delivery_zone = 'Outer Metro'
                    self.delivery_cost = Decimal('81.80')
                else:
                    self.delivery_zone = 'Regional'
                    self.delivery_cost = Decimal('150.00')
            else:
                # Non-steel products use NEW zone pricing
                excel_path = os.path.join(settings.BASE_DIR, 'SA_by_zones.xlsx')  # FIXED: No quotes folder
                df = pd.read_excel(excel_path)

                row = df.loc[df['Postcode'].astype(str) == str(self.delivery_postcode)].iloc[0]
                zone = str(row['Zones']).strip()

                # New zone pricing for non-steel products
                pricing = {
                    '1': Decimal('143.50'),
                    '2': Decimal('181.50'),
                    '3': Decimal('242.00'),
                    '4': Decimal('302.50'),
                    '5': Decimal('0.00')  # POA
                }

                self.delivery_zone = f'Zone {zone}'
                self.delivery_cost = pricing.get(zone, Decimal('0.00'))

        except Exception as e:
            print(f"❌ Delivery calculation error: {str(e)}")  # Debug
            self.delivery_zone = 'Unknown'
            self.delivery_cost = Decimal('0.00')

        self.save()
        return self.delivery_cost



class DeliveryTemplate(models.Model):
    """Template for recurring delivery slots"""

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    name = models.CharField(max_length=100, help_text="Template name (e.g., 'Weekday Morning Deliveries')")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    time_slot = models.CharField(max_length=50)  # e.g., "9:00 AM - 12:00 PM"
    capacity = models.PositiveIntegerField(default=5)

    delivery_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Delivery'),
        ('external', 'External Partner'),
        ('pickup', 'Customer Pickup'),
        ('Both Available', 'Both Available')
    ], default='Both Available')

    is_active = models.BooleanField(default=True, help_text="Generate slots for this template")
    notes = models.TextField(blank=True)

    # Advanced scheduling
    exclude_dates = models.TextField(
        blank=True,
        help_text="Comma-separated dates to exclude (YYYY-MM-DD format). E.g., 2024-12-25,2024-01-01"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'time_slot']
        unique_together = ['day_of_week', 'time_slot', 'delivery_type']

    def __str__(self):
        return f"{self.name} - {self.get_day_of_week_display()} {self.time_slot}"

    def get_excluded_dates(self):
        """Parse excluded dates string into date objects"""
        if not self.exclude_dates:
            return []

        excluded = []
        for date_str in self.exclude_dates.split(','):
            try:
                date_obj = timezone.datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                excluded.append(date_obj)
            except ValueError:
                continue
        return excluded


class DeliverySlot(models.Model):
    """Available delivery slots with enhanced management"""
    date = models.DateField()
    time_slot = models.CharField(max_length=50)  # e.g., "9:00 AM - 12:00 PM"
    capacity = models.PositiveIntegerField(default=5)  # Max orders per slot
    is_available = models.BooleanField(default=True)

    # Enhanced fields
    delivery_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Delivery'),
        ('external', 'External Partner'),
        ('pickup', 'Customer Pickup'),
        ('Both Available', 'Both Available')
    ], default='Both Available')

    notes = models.TextField(blank=True, help_text="Internal notes about this time slot")
    created_by = models.CharField(max_length=100, blank=True)

    # NEW: Link to template for auto-generated slots
    template = models.ForeignKey(
        DeliveryTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template used to generate this slot (if auto-generated)"
    )
    is_auto_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'time_slot', 'delivery_type']
        ordering = ['date', 'time_slot']

    def __str__(self):
        return f"{self.date} {self.time_slot} ({self.delivery_type})"

    @property
    def orders_count(self):
        return Order.objects.filter(delivery_slot=self).count()

    @property
    def available_capacity(self):
        return self.capacity - self.orders_count

    @property
    def is_full(self):
        return self.orders_count >= self.capacity

class Order(models.Model):
    """Main order record WITH DISCOUNT SUPPORT"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Delivery Pending'),
        ('accepted', 'Delivery Accepted'),
        ('rejected', 'Delivery Rejected'),
        ('outsourced', 'Passed to RB Transport'),
        ('scheduled', 'Delivery Scheduled'),
        ('completed', 'Delivery Completed'),
    ]

    # Basic order info
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # 🎯 DISCOUNT FIELDS (ADDED!)
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_type = models.CharField(max_length=20, blank=True)

    # Payment info
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, default='stripe')
    paid_at = models.DateTimeField(null=True, blank=True)

    # Xero integration
    xero_invoice_id = models.CharField(max_length=200, blank=True)
    xero_invoice_number = models.CharField(max_length=100, blank=True)
    xero_synced_at = models.DateTimeField(null=True, blank=True)

    # Enhanced Delivery Management
    delivery_slot = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    delivery_notes = models.TextField(blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time_slot = models.CharField(max_length=50, blank=True)  # e.g., "9:00 AM - 12:00 PM"
    tracking_number = models.CharField(max_length=100, blank=True)

    # RB Transport Integration
    rb_transport_sent = models.BooleanField(default=False)
    rb_transport_sent_at = models.DateTimeField(null=True, blank=True)
    rb_transport_response = models.TextField(blank=True)

    # Internal delivery management
    internal_delivery_assigned_to = models.CharField(max_length=100, blank=True)
    delivery_vehicle = models.CharField(max_length=100, blank=True)
    delivery_instructions = models.TextField(blank=True)

    special_requests = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="Customer special requirements like sleeper cutting, delivery instructions, etc.",
        verbose_name="Special Requests"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = f"WQ{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_weight(self):
        """Calculate total weight of all items in kg using real database weights"""
        total_weight = 0

        for item in self.items.all():
            # Get weight for this item (tries database first, then fallback)
            item_weight = self.get_item_weight(item)
            total_weight += item_weight * item.quantity

        return total_weight

    def get_item_weight(self, item):
        """Get estimated weight for a single item in kg - now uses database first"""

        # STEP 1: Try to get weight from database using SKU/item code
        if hasattr(item, 'product_id') and item.product_id:
            try:
                product = Product.objects.filter(sku=item.product_id, is_active=True).first()
                if product and product.weight > 0:
                    return float(product.weight)
            except Exception:
                pass

        # STEP 2: Try to match by product name in database
        if item.product_name:
            try:
                # Try exact name match first
                product = Product.objects.filter(name__iexact=item.product_name, is_active=True).first()
                if product and product.weight > 0:
                    return float(product.weight)

                # Try partial name match (first word)
                first_word = item.product_name.split()[0]
                product = Product.objects.filter(name__icontains=first_word, is_active=True).first()
                if product and product.weight > 0:
                    return float(product.weight)
            except Exception:
                pass

        # STEP 3: Fallback to estimated weights (your original logic but fixed)
        product_name_lower = item.product_name.lower()

        # Fix: Handle None product_thickness properly
        thickness = None
        if item.product_thickness:
            thickness = item.product_thickness.replace('mm', '')

        # Estimated weights based on product type (fallback only)
        if any(x in product_name_lower for x in ['ashwood', 'sleeper']):
            if thickness == '100':
                return 80
            elif thickness == '130':
                return 130
            else:
                return 60  # Default for 75-80mm

        elif 'blackwood' in product_name_lower:
            if thickness == '100':
                return 82
            else:
                return 62

        elif 'cove' in product_name_lower:
            if thickness == '100':
                return 78
            else:
                return 58

        elif 'lonsdale' in product_name_lower:
            if thickness == '100':
                return 80
            else:
                return 60

        elif 'kensington' in product_name_lower:
            if thickness == '100':
                return 85
            else:
                return 65

        elif 'mclaren' in product_name_lower:
            return 85  # Only comes in 100mm

        elif 'diy' in product_name_lower:
            if thickness == '100':
                return 73
            else:
                return 55

        elif 'ufp' in product_name_lower:
            return 40

        elif 'post' in product_name_lower:
            if 'h post' in product_name_lower:
                return 20
            elif 'corner' in product_name_lower:
                return 22
            else:
                return 16  # c-post

        elif 'step' in product_name_lower:
            return 80

        elif 'wheel' in product_name_lower:
            return 45

        else:
            return 60  # Default weight

    def calculate_totals(self):
        """Recalculate order totals including discounts"""
        self.subtotal = sum(item.total_price for item in self.items.all())

        # Apply discount if present
        discounted_subtotal = self.subtotal - self.discount_amount

        # Handle free shipping discount
        if self.discount_type == 'free_shipping':
            self.delivery_cost = Decimal('0.00')
        else:
            self.delivery_cost = self.customer.delivery_cost

        # GST calculation (10% in Australia) - applied to discounted amount
        self.tax_amount = (discounted_subtotal + self.delivery_cost) * Decimal('0.10')
        self.total_amount = discounted_subtotal + self.delivery_cost + self.tax_amount
        self.save()

    def send_to_rb_transport(self):
        """Send order details to RB Transport using automation instead of email"""
        from .rb_transport_utils import submit_order_to_rb_transport

        try:
            success = submit_order_to_rb_transport(self)

            if success:
                self.delivery_status = 'outsourced'
                self.rb_transport_sent = True
                self.rb_transport_sent_at = timezone.now()
                self.rb_transport_response = "Successfully submitted via automation portal"
                self.save()
                return True
            else:
                self.rb_transport_response = "Automation failed - form submission unsuccessful"
                self.save()
                return False

        except Exception as e:
            self.rb_transport_response = f"Automation error: {str(e)}"
            self.save()
            return False

    def estimate_volume(self):
        """Estimate total volume for transport planning"""
        # Rough calculation based on typical sleeper dimensions
        total_items = self.total_items
        if total_items <= 5:
            return "Small load (fits in ute)"
        elif total_items <= 15:
            return "Medium load (small truck required)"
        else:
            return "Large load (truck with crane required)"


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # Product info (snapshot at time of order)
    product_id = models.CharField(max_length=50)  # From products_data.py
    product_name = models.CharField(max_length=200)
    product_length = models.CharField(max_length=20, blank=True)
    product_thickness = models.CharField(max_length=20, blank=True)
    product_style = models.CharField(max_length=100, blank=True)

    # Pricing at time of order
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Additional details
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} @ ${self.unit_price}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class DiscountUsage(models.Model):
    """Track discount code usage"""

    discount_code = models.ForeignKey(DiscountCode, on_delete=models.CASCADE, related_name='usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    customer_email = models.EmailField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.discount_code.code} used by {self.customer_email} - ${self.discount_amount}"


class ProductCategory(models.Model):
    """Main product categories"""
    CATEGORY_CHOICES = [
        ('galvanised_steel', 'Galvanised Steel'),
        ('concrete_sleepers', 'Concrete Sleepers'),
        ('concrete_ufp_cribs', 'Concrete UFPs and Cribs'),
        ('step_kits', 'Step Kits'),
        ('accessories', 'Accessories'),
    ]

    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name


class ProductGroup(models.Model):
    """Product groups within categories (e.g., different colors for sleepers)"""
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)  # e.g., "Plain Grey", "Charcoal Stackstone"
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='product_groups/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'sort_order', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.display_name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.name}-{self.name}")
        super().save(*args, **kwargs)


class Brand(models.Model):
    """Brands (OS - Outback Sleepers, SC - Silvercrete)"""
    code = models.CharField(max_length=10, unique=True)  # 'OS' or 'SC'
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProductVariant(models.Model):
    """Individual product variants with all specifications"""

    # Core relationships
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, related_name='variants')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')

    # Product identification
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)  # Full descriptive name

    # Specifications (all optional as different products have different specs)
    length = models.CharField(max_length=20, blank=True)  # e.g., "2.0m", "2.4m"
    height = models.CharField(max_length=20, blank=True)  # e.g., "200", "150"
    thickness = models.CharField(max_length=20, blank=True)  # e.g., "75", "80", "100"
    width = models.CharField(max_length=20, blank=True)

    # Additional specs for special products
    is_rebated = models.BooleanField(default=False)  # For UFPs
    is_tapered = models.BooleanField(default=False)  # For some sleepers
    smooth_finish = models.CharField(max_length=20, blank=True)  # "one-sided", "double-sided"
    opening_size = models.CharField(max_length=20, blank=True)  # For step kits

    # Pricing (EXCLUDING GST as requested)
    price_ex_gst = models.DecimalField(max_digits=10, decimal_places=2)

    # Product details
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Weight in kg")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Excel source tracking
    excel_row_reference = models.CharField(max_length=50, blank=True, help_text="Reference to Excel row for syncing")
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['product_group', 'brand', 'length', 'height', 'thickness']

    def __str__(self):
        return f"{self.brand.code} {self.product_group.name} - {self.get_specs_display()}"

    def get_specs_display(self):
        """Generate display string for specifications"""
        specs = []
        if self.length:
            specs.append(self.length)
        if self.height:
            specs.append(f"H{self.height}")
        if self.thickness:
            specs.append(f"T{self.thickness}")
        if self.is_rebated:
            specs.append("Rebated")
        if self.is_tapered:
            specs.append("Tapered")
        return " × ".join(specs) if specs else "Standard"

    @property
    def price_inc_gst(self):
        """Calculate price including GST (10%)"""
        return self.price_ex_gst * Decimal('1.10')


class ExcelSyncLog(models.Model):
    """Track Excel file synchronization"""
    file_name = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    last_modified = models.DateTimeField()
    sync_started = models.DateTimeField(auto_now_add=True)
    sync_completed = models.DateTimeField(null=True, blank=True)
    products_created = models.PositiveIntegerField(default=0)
    products_updated = models.PositiveIntegerField(default=0)
    errors = models.TextField(blank=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"Sync {self.file_name} - {self.sync_started.strftime('%Y-%m-%d %H:%M')}"





