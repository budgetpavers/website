from django.contrib import admin
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from datetime import date
from django.utils import timezone

from .models import QuoteRequest, Product, FAQ, BlogPost, Customer, Order, OrderItem, DeliverySlot
from .models import DiscountCode, DiscountableProduct, DiscountUsage, DeliveryTemplate
from .rb_transport_utils import submit_order_to_rb_transport

# ——————————————————————————
# QuoteRequest Admin
@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'customer_email', 'phone',
        'calculator_type',
        'wall_length', 'wall_height', 'fence_length', 'plinths_per_panel',
        'total_sleepers', 'total_plinths', 'steel_posts_required',
        'estimated_cost', 'delivery_zone', 'delivery_cost', 'total_cost_display',
        'has_custom_message',  # NEW FIELD INDICATOR
        'status', 'created_at',
    )
    list_editable = ('status',)
    list_filter = ('status', 'created_at', 'calculator_type')
    search_fields = ('customer_name', 'customer_email', 'delivery_address', 'phone', 'custom_message')  # Added custom_message to search
    actions = ['mark_as_approved', 'mark_as_paid', 'mark_as_declined']

    # Add fieldsets to organize the admin form better
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'phone', 'delivery_address')
        }),
        ('Quote Details', {
            'fields': ('calculator_type', 'wall_length', 'wall_height', 'fence_length', 'plinths_per_panel')
        }),
        ('Pricing', {
            'fields': ('estimated_cost', 'delivery_zone', 'delivery_cost')
        }),
        ('Customer Message', {
            'fields': ('custom_message',),
            'classes': ('wide',),
            'description': 'Additional notes or requirements from the customer'
        }),
        ('Status', {
            'fields': ('status', 'preferred_date', 'created_at')
        }),
    )

    readonly_fields = ('created_at',)

    @admin.display(description="Total Cost")
    def total_cost_display(self, obj):
        if obj.estimated_cost and obj.delivery_cost:
            return f"${obj.estimated_cost + obj.delivery_cost:.2f}"
        elif obj.estimated_cost:
            return f"${obj.estimated_cost:.2f}"
        return "-"

    @admin.display(description="Has Message", boolean=True)
    def has_custom_message(self, obj):
        return bool(obj.custom_message and obj.custom_message.strip())

    @admin.action(description="Mark selected as Approved")
    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description="Mark selected as Paid")
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')

    @admin.action(description="Mark selected as Declined")
    def mark_as_declined(self, request, queryset):
        queryset.update(status='declined')

# Custom filter for special requests
class HasSpecialRequestsFilter(admin.SimpleListFilter):
    title = 'has special requests'
    parameter_name = 'has_special_requests'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Special Requests'),
            ('no', 'No Special Requests'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                special_requests__isnull=False
            ).exclude(special_requests__exact='')
        if self.value() == 'no':
            from django.db import models
            return queryset.filter(
                models.Q(special_requests__isnull=True) |
                models.Q(special_requests__exact='')
            )
        return queryset

# ——————————————————————————
# Order Item Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product_name', 'product_length', 'product_thickness', 'quantity', 'unit_price', 'total_price')


# ——————————————————————————
# Customer Admin
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'delivery_zone', 'delivery_cost', 'order_count', 'created_at')
    list_filter = ('delivery_zone', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'created_at')
        }),
        ('Billing Address', {
            'fields': ('billing_address_line1', 'billing_city', 'billing_state', 'billing_postcode')
        }),
        ('Delivery Address', {
            'fields': ('delivery_address_line1', 'delivery_city', 'delivery_state', 'delivery_postcode')
        }),
        ('Delivery Information', {
            'fields': ('delivery_zone', 'delivery_cost')
        }),
    )

    def order_count(self, obj):
        return obj.orders.count()

    order_count.short_description = "Orders"


# ——————————————————————————
# Enhanced Order Admin with Discount Support
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer_name', 'status', 'delivery_status_display', 'delivery_date',
        'discount_display', 'has_special_requests', 'total_amount', 'total_weight_display', 'delivery_actions'
    )
    list_filter = (
        'status', 'delivery_status', 'created_at', 'customer__delivery_zone', 'payment_method',
        'delivery_date', 'discount_code', HasSpecialRequestsFilter
    )
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name', 'customer__email', 'special_requests')
    readonly_fields = (
        'order_number', 'created_at', 'updated_at', 'stripe_payment_intent_id', 'total_items', 'total_weight',
        'rb_transport_sent_at'
    )
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped', 'mark_as_delivered', 'accept_delivery', 'reject_delivery', 'send_to_rb_transport',
               'generate_packing_slips' , 'export_special_requests']

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'created_at', 'updated_at')
        }),
        ('Payment Information', {
            'fields': ('stripe_payment_intent_id', 'payment_method', 'paid_at')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_cost', 'tax_amount', 'total_amount', 'total_items', 'total_weight')
        }),
        ('Discount Information', {
            'fields': ('discount_code', 'discount_amount', 'discount_type'),
            'classes': ('wide',)
        }),
        ('Delivery Management', {
            'fields': ('delivery_slot', 'delivery_status', 'delivery_date', 'delivery_time_slot', 'delivery_notes',
                       'tracking_number'),
            'classes': ('wide',)
        }),
        ('Internal Delivery', {
            'fields': ('internal_delivery_assigned_to', 'delivery_vehicle', 'delivery_instructions'),
            'classes': ('collapse',)
        }),
        ('RB Transport Integration', {
            'fields': ('rb_transport_sent', 'rb_transport_sent_at', 'rb_transport_response'),
            'classes': ('collapse',)
        }),
        ('Xero Integration', {
            'fields': ('xero_invoice_id', 'xero_invoice_number', 'xero_synced_at'),
            'classes': ('collapse',)
        }),
        ('Special Requests', {
            'fields': ('special_requests',),
            'classes': ('wide',),
            'description': 'Customer special requirements like sleeper cutting, delivery instructions, etc.'
        }),


    )

    def customer_name(self, obj):
        return obj.customer.full_name

    customer_name.short_description = "Customer"

    def discount_display(self, obj):
        if obj.discount_code:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} (-${})</span>',
                obj.discount_code.code,
                obj.discount_amount
            )
        return "-"

    discount_display.short_description = "Discount"

    def delivery_status_display(self, obj):
        colors = {
            'pending': '#ffc107',  # Yellow
            'accepted': '#28a745',  # Green
            'rejected': '#dc3545',  # Red
            'outsourced': '#17a2b8',  # Blue
            'scheduled': '#6f42c1',  # Purple
            'completed': '#20c997',  # Teal
        }
        color = colors.get(obj.delivery_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_delivery_status_display()
        )

    delivery_status_display.short_description = "Delivery Status"

    def total_weight_display(self, obj):
        """Display total weight with proper units and formatting"""
        weight = obj.total_weight

        if weight >= 1000:
            # Show in tonnes for weights 1000kg and above
            tonnes = weight / 1000
            return f"{tonnes:.1f}t"
        elif weight > 0:
            # Show in kg for weights below 1000kg
            return f"{weight:.0f}kg"
        else:
            # Handle zero or negative weights
            return "0kg"

    total_weight_display.short_description = "Weight"

    def delivery_actions(self, obj):
        actions = []

        # Packing slip
        packing_url = reverse('admin:generate_packing_slip', args=[obj.pk])
        actions.append(f'<a href="{packing_url}" class="button" style="margin:2px;">📄 Slip</a>')

        if obj.special_requests and obj.special_requests.strip():
            actions.append(
                f'<span style="color:#ff6b35; font-weight:bold; margin:2px;" title="{obj.special_requests[:100]}">📝 Requests</span>')

        if obj.delivery_status == 'pending':
            # Accept delivery
            accept_url = reverse('admin:accept_delivery', args=[obj.pk])
            actions.append(
                f'<a href="{accept_url}" class="button" style="margin:2px; background:#28a745; color:white;">✅ Accept</a>')

            # Reject delivery
            reject_url = reverse('admin:reject_delivery', args=[obj.pk])
            actions.append(
                f'<a href="{reject_url}" class="button" style="margin:2px; background:#dc3545; color:white;">❌ Reject</a>')

            # Send to RB Transport - UPDATED WITH AUTOMATION INDICATOR
            rb_url = reverse('admin:send_to_rb_transport', args=[obj.pk])
            actions.append(
                f'<a href="{rb_url}" class="button" style="margin:2px; background:#17a2b8; color:white;">🤖 RB Transport</a>')

        elif obj.delivery_status == 'outsourced':
            actions.append('<span style="color:#17a2b8; font-weight:bold;">🤖 Sent to RB Transport (Auto)</span>')

        elif obj.delivery_status == 'accepted':
            actions.append('<span style="color:#28a745; font-weight:bold;">✅ Accepted for Internal Delivery</span>')

        return format_html(' '.join(actions))

    delivery_actions.short_description = "Actions"
    delivery_actions.allow_tags = True

    # Bulk Actions
    @admin.action(description="✅ Accept delivery (internal)")
    def accept_delivery(self, request, queryset):
        updated = queryset.update(delivery_status='accepted')
        self.message_user(request, f"Accepted delivery for {updated} orders.")

    @admin.action(description="❌ Reject delivery")
    def reject_delivery(self, request, queryset):
        updated = queryset.update(delivery_status='rejected')
        self.message_user(request, f"Rejected delivery for {updated} orders.")

    @admin.action(description="🤖 Send to RB Transport Portal (Automation)")
    def send_to_rb_transport(self, request, queryset):
        success_count = 0
        failed_count = 0

        for order in queryset:
            try:
                # Use your new automation instead of the old email method
                if submit_order_to_rb_transport(order):
                    order.delivery_status = 'outsourced'
                    order.rb_transport_sent = True
                    order.rb_transport_sent_at = timezone.now()
                    order.rb_transport_response = "Successfully submitted via automation portal"
                    order.save()
                    success_count += 1
                else:
                    order.rb_transport_response = "Automation failed - form submission unsuccessful"
                    order.save()
                    failed_count += 1
            except Exception as e:
                order.rb_transport_response = f"Automation error: {str(e)}"
                order.save()
                failed_count += 1

        if success_count > 0:
            self.message_user(request,
                              f"🤖 Successfully submitted {success_count} orders to RB Transport portal via automation.")
        if failed_count > 0:
            self.message_user(request,
                              f"❌ Failed to submit {failed_count} orders. Check individual order notes for details.",
                              level=messages.ERROR)

    @admin.action(description="Mark as shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped', delivery_status='scheduled')
        self.message_user(request, f"Marked {queryset.count()} orders as shipped.")

    @admin.action(description="Mark as delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', delivery_status='completed')
        self.message_user(request, f"Marked {queryset.count()} orders as delivered.")

    @admin.action(description="Generate packing slips")
    def generate_packing_slips(self, request, queryset):
        self.message_user(request, f"Generated packing slips for {queryset.count()} orders.")

    def has_special_requests(self, obj):
        """Display if order has special requests"""
        if obj.special_requests and obj.special_requests.strip():
            return format_html(
                '<span style="color: #ff6b35; font-weight: bold;" title="{}">📝 Yes</span>',
                obj.special_requests[:100] + ('...' if len(obj.special_requests) > 100 else '')
            )
        return format_html('<span style="color: #6c757d;">—</span>')

    has_special_requests.short_description = "Special Requests"
    has_special_requests.admin_order_field = 'special_requests'

    @admin.action(description="📋 Export Special Requests Report")
    def export_special_requests(self, request, queryset):
        """Export orders with special requests to CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime

        # Filter only orders with special requests
        orders_with_requests = queryset.filter(
            special_requests__isnull=False
        ).exclude(special_requests__exact='')

        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="special_requests_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Order Number', 'Customer Name', 'Email', 'Phone',
            'Status', 'Delivery Status', 'Created Date', 'Special Requests'
        ])

        for order in orders_with_requests:
            writer.writerow([
                order.order_number,
                order.customer.full_name,
                order.customer.email,
                order.customer.phone or '',
                order.get_status_display(),
                order.get_delivery_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.special_requests
            ])

        self.message_user(request, f"Exported {orders_with_requests.count()} orders with special requests.")
        return response


# ——————————————————————————


# ——————————————————————————
# Order Item Admin
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'product_name', 'product_length', 'product_thickness', 'quantity', 'unit_price', 'total_price'
    )
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product_name', 'order__order_number', 'order__customer__email')
    readonly_fields = ('total_price',)


# ——————————————————————————
# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'weight', 'is_active', 'has_image')
    list_filter = ('category', 'is_active', 'color')
    search_fields = ('name', 'sku', 'description')
    list_editable = ('price', 'is_active')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'category', 'color')
        }),
        ('Pricing & Weight', {
            'fields': ('price', 'weight')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def has_image(self, obj):
        return bool(obj.image)

    has_image.boolean = True
    has_image.short_description = 'Has Image'


# ——————————————————————————
# FAQ Admin
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'short_answer', 'order')
    list_editable = ('order',)
    search_fields = ('question', 'answer')

    def short_answer(self, obj):
        return obj.answer[:75] + ("..." if len(obj.answer) > 75 else "")
    short_answer.short_description = "Answer"


# ——————————————————————————
# BlogPost Admin
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at', 'updated_at')
    list_editable = ('published',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}


# ——————————————————————————
# DISCOUNT ADMIN CLASSES
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'discount_type', 'discount_value', 'times_used_display',
        'max_uses', 'is_active', 'valid_from', 'valid_until', 'status_display'
    )
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until', 'created_at')
    search_fields = ('code', 'name', 'description')
    list_editable = ('is_active',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value'),
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'max_uses_per_customer', 'minimum_order_amount'),
        }),
        ('Date Restrictions', {
            'fields': ('valid_from', 'valid_until'),
        }),
        ('Product Restrictions', {
            'fields': ('applicable_products', 'exclude_products'),
            'description': 'Select specific products to include/exclude from this discount.',
        }),
        ('Category Restrictions', {
            'fields': ('applicable_categories', 'exclude_categories'),
            'description': 'Use categories for broader control. Examples: "Steel,Sleepers" or "Accessories"',
        }),
    )

    filter_horizontal = ('applicable_products', 'exclude_products')

    def times_used_display(self, obj):
        used = obj.times_used
        max_uses = obj.max_uses or "∞"
        color = "green" if used < (obj.max_uses or 999999) else "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color, used, max_uses
        )

    times_used_display.short_description = "Usage"

    def status_display(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: red;">❌ Inactive</span>')
        elif not obj.is_valid_now:
            return format_html('<span style="color: orange;">⏰ Expired/Future</span>')
        else:
            return format_html('<span style="color: green;">✅ Active</span>')

    status_display.short_description = "Status"

    actions = ['activate_codes', 'deactivate_codes', 'test_discount_calculation']

    @admin.action(description="Activate selected discount codes")
    def activate_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} discount codes.")

    @admin.action(description="Deactivate selected discount codes")
    def deactivate_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} discount codes.")

    @admin.action(description="🧪 Test discount calculation")
    def test_discount_calculation(self, request, queryset):
        """Test discount calculation with sample cart"""
        from decimal import Decimal

        # Create sample cart items using real products
        sample_products = Product.objects.filter(is_active=True)[:3]
        test_cart = []

        for product in sample_products:
            test_cart.append({
                'product_id': str(product.id),
                'cart_key': str(product.id),
                'name': product.name,
                'total': Decimal('100.00'),  # Sample total
            })

        subtotal = Decimal('300.00')
        delivery_cost = Decimal('68.18')

        for discount in queryset:
            discount_amount = discount.calculate_discount(test_cart, subtotal, delivery_cost)
            self.message_user(
                request,
                f"💰 {discount.code}: Would give ${discount_amount:.2f} discount on sample $300 cart"
            )


@admin.register(DiscountableProduct)
class DiscountableProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'name', 'category', 'mapped_product', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('product_id', 'name', 'category')
    readonly_fields = ('product_id', 'name', 'category', 'created_at', 'updated_at')

    fieldsets = (
        ('Legacy Information', {
            'fields': ('product_id', 'name', 'category', 'created_at', 'updated_at'),
            'description': 'This is legacy data from products_data.py'
        }),
        ('New Mapping', {
            'fields': ('mapped_product',),
            'description': 'Map this legacy product to a new Product model entry'
        }),
    )

    actions = ['map_to_database_products', 'delete_unmapped_legacy']

    @admin.action(description="🔗 Map legacy products to database products")
    def map_to_database_products(self, request, queryset):
        """Attempt to automatically map legacy products to database products"""
        mapped_count = 0

        for legacy_product in queryset:
            if legacy_product.mapped_product:
                continue  # Already mapped

            # Try to find matching database product by name similarity
            potential_matches = Product.objects.filter(
                name__icontains=legacy_product.name.split()[0],  # First word match
                is_active=True
            )

            if potential_matches.count() == 1:
                legacy_product.mapped_product = potential_matches.first()
                legacy_product.save()
                mapped_count += 1

        self.message_user(request, f"🔗 Automatically mapped {mapped_count} legacy products to database products.")

    @admin.action(description="🗑️ Delete unmapped legacy products")
    def delete_unmapped_legacy(self, request, queryset):
        """Delete legacy products that haven't been mapped"""
        unmapped = queryset.filter(mapped_product__isnull=True)
        count = unmapped.count()
        unmapped.delete()
        self.message_user(request, f"🗑️ Deleted {count} unmapped legacy products.")

    def has_add_permission(self, request):
        # Prevent adding new legacy products
        return False


@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    list_display = ('discount_code', 'customer_email', 'order', 'discount_amount', 'used_at')
    list_filter = ('discount_code', 'used_at')
    search_fields = ('discount_code__code', 'customer_email', 'order__order_number')
    readonly_fields = ('used_at',)

    def has_add_permission(self, request):
        # Prevent manual creation of usage records
        return False


# ——————————————————————————
# DELIVERY TEMPLATE ADMIN (NEW)
@admin.register(DeliveryTemplate)
class DeliveryTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'day_of_week_display', 'time_slot', 'delivery_type',
        'capacity', 'is_active', 'upcoming_slots_count'
    )
    list_filter = ('day_of_week', 'delivery_type', 'is_active', 'created_at')
    list_editable = ('is_active', 'capacity')
    search_fields = ('name', 'time_slot', 'notes')

    fieldsets = (
        ('Template Details', {
            'fields': ('name', 'day_of_week', 'time_slot', 'capacity', 'delivery_type')
        }),
        ('Settings', {
            'fields': ('is_active', 'notes')
        }),
        ('Exclusions', {
            'fields': ('exclude_dates',),
            'description': 'Enter dates to exclude in YYYY-MM-DD format, separated by commas (e.g., 2024-12-25,2024-01-01)'
        }),
    )

    actions = ['generate_slots_for_week', 'activate_templates', 'deactivate_templates']

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = "Day"

    def upcoming_slots_count(self, obj):
        """Show how many slots will be generated in the next week"""
        from datetime import date, timedelta

        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)

        count = 0
        current_date = start_date
        excluded_dates = obj.get_excluded_dates()

        while current_date <= end_date:
            if (current_date.weekday() == obj.day_of_week and
                    current_date not in excluded_dates):
                # Check if slot doesn't already exist
                if not DeliverySlot.objects.filter(
                        date=current_date,
                        time_slot=obj.time_slot,
                        delivery_type=obj.delivery_type
                ).exists():
                    count += 1
            current_date += timedelta(days=1)

        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} new</span>', count)
        else:
            return format_html('<span style="color: gray;">0 new</span>')
    upcoming_slots_count.short_description = "Next Week"

    @admin.action(description="🚛 Generate slots for next week")
    def generate_slots_for_week(self, request, queryset):
        from django.core.management import call_command
        from io import StringIO

        # Capture command output
        out = StringIO()
        call_command('generate_delivery_slots', days=7, stdout=out)
        output = out.getvalue()

        # Show results to admin
        self.message_user(request, f"Generated delivery slots! Output: {output}")

    @admin.action(description="Activate selected templates")
    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} templates.")

    @admin.action(description="Deactivate selected templates")
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} templates.")


# ——————————————————————————
# DELIVERY SLOT ADMIN (UPDATED)
@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'time_slot', 'delivery_type', 'capacity', 'orders_count',
        'available_capacity', 'is_available', 'is_auto_generated', 'is_full_display'
    )
    list_filter = (
        'date', 'is_available', 'delivery_type', 'is_auto_generated',
        'template__name', 'created_at'
    )
    list_editable = ('is_available', 'capacity')
    search_fields = ('date', 'time_slot', 'notes')
    readonly_fields = ('orders_count', 'available_capacity', 'created_at')

    fieldsets = (
        ('Slot Details', {
            'fields': ('date', 'time_slot', 'delivery_type', 'capacity', 'is_available')
        }),
        ('Booking Info', {
            'fields': ('orders_count', 'available_capacity'),
            'classes': ('collapse',)
        }),
        ('Template Info', {
            'fields': ('template', 'is_auto_generated', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['generate_this_week', 'cleanup_old_slots', 'mark_unavailable', 'mark_available']

    def get_queryset(self, request):
        """Only show slots for the next 2 weeks by default"""
        from datetime import date, timedelta

        qs = super().get_queryset(request)

        # Default filter: show only upcoming slots (next 14 days)
        if not request.GET.get('date__gte') and not request.GET.get('date__lte'):
            start_date = date.today()
            end_date = start_date + timedelta(days=14)
            qs = qs.filter(date__gte=start_date, date__lte=end_date)

        return qs

    def is_full_display(self, obj):
        if obj.is_full:
            return format_html('<span style="color: red; font-weight: bold;">🔴 FULL</span>')
        elif obj.available_capacity <= 2:
            return format_html('<span style="color: orange; font-weight: bold;">🟡 LIMITED</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">🟢 Available</span>')
    is_full_display.short_description = "Status"

    @admin.action(description="🚛 Generate slots for this week")
    def generate_this_week(self, request, queryset):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('generate_delivery_slots', days=7, stdout=out)
        output = out.getvalue()

        self.message_user(request, f"Generated delivery slots! Check the output in console.")

    @admin.action(description="🗑️ Clean up old slots")
    def cleanup_old_slots(self, request, queryset):
        from datetime import date

        old_count = DeliverySlot.objects.filter(
            date__lt=date.today(),
            is_auto_generated=True
        ).count()

        DeliverySlot.objects.filter(
            date__lt=date.today(),
            is_auto_generated=True
        ).delete()

        self.message_user(request, f"Cleaned up {old_count} old auto-generated slots.")

    @admin.action(description="Mark as unavailable")
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f"Marked {updated} slots as unavailable.")

    @admin.action(description="Mark as available")
    def mark_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f"Marked {updated} slots as available.")


# ——————————————————————————
# Delivery Management Action Views
def accept_delivery_view(request, order_id):
    """Accept delivery for internal handling"""
    order = get_object_or_404(Order, pk=order_id)
    order.delivery_status = 'accepted'
    order.save()

    messages.success(request, f"✅ Delivery accepted for order {order.order_number}")
    return redirect('admin:quotes_order_change', order_id)


def reject_delivery_view(request, order_id):
    """Reject delivery - customer needs to choose new slot"""
    order = get_object_or_404(Order, pk=order_id)
    order.delivery_status = 'rejected'
    order.save()

    # TODO: Send email to customer to choose new delivery slot
    messages.warning(request, f"❌ Delivery rejected for order {order.order_number}. Customer will be notified.")
    return redirect('admin:quotes_order_change', order_id)


@admin.action(description="🤖 Send to RB Transport Portal (Automation)")
def send_to_rb_transport(self, request, queryset):
    success_count = 0
    failed_count = 0

    for order in queryset:
        try:
            # Use your new automation instead of the old email method
            if submit_order_to_rb_transport(order):
                order.delivery_status = 'outsourced'
                order.rb_transport_sent = True
                order.rb_transport_sent_at = timezone.now()
                order.rb_transport_response = "Successfully submitted via automation portal"
                order.save()
                success_count += 1
            else:
                order.rb_transport_response = "Automation failed - form submission unsuccessful"
                order.save()
                failed_count += 1
        except Exception as e:
            order.rb_transport_response = f"Automation error: {str(e)}"
            order.save()
            failed_count += 1

    if success_count > 0:
        self.message_user(request, f"🤖 Successfully submitted {success_count} orders to RB Transport portal via automation.")
    if failed_count > 0:
        self.message_user(request, f"❌ Failed to submit {failed_count} orders. Check individual order notes for details.", level=messages.ERROR)


def send_to_rb_transport_view(request, order_id):
    """Send order to RB Transport using NEW AUTOMATION"""
    order = get_object_or_404(Order, pk=order_id)

    try:
        # Use your new automation instead of email
        success = submit_order_to_rb_transport(order)

        if success:
            # Update order status
            order.delivery_status = 'outsourced'
            order.rb_transport_sent = True
            order.rb_transport_sent_at = timezone.now()
            order.rb_transport_response = "Successfully submitted via automation portal"
            order.save()

            messages.success(request, f"🤖 Order {order.order_number} submitted to RB Transport portal successfully!")
        else:
            order.rb_transport_response = "Automation failed - form submission unsuccessful"
            order.save()
            messages.error(request, f"❌ Failed to submit order {order.order_number} to RB Transport portal.")

    except Exception as e:
        order.rb_transport_response = f"Automation error: {str(e)}"
        order.save()
        messages.error(request, f"❌ Error submitting to RB Transport: {str(e)}")

    return redirect('admin:quotes_order_change', order_id)


# ——————————————————————————
# Packing Slip PDF Generation
def generate_packing_slip(request, order_id):
    """Generate PDF packing slip for an order"""
    order = get_object_or_404(Order, pk=order_id)

    # For now, return HTML version - we'll add PDF generation next
    from django.template.loader import render_to_string
    html_content = render_to_string('admin/packing_slip.html', {'order': order})
    return HttpResponse(html_content)


# ——————————————————————————
# Custom Admin Index (Enhanced)
_original_index = admin.site.index


def custom_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}

    # Your existing quote data
    extra_context['pending_quotes'] = QuoteRequest.objects.filter(status='pending').order_by('-created_at')[:10]
    extra_context['approved_requests'] = QuoteRequest.objects.filter(status='approved').order_by('preferred_date')[:10]
    extra_context['today'] = date.today()

    # NEW: Add order statistics
    extra_context['recent_orders'] = Order.objects.order_by('-created_at')[:10]
    extra_context['processing_orders'] = Order.objects.filter(status='processing').count()
    extra_context['pending_deliveries'] = Order.objects.filter(delivery_status='pending').count()
    extra_context['shipped_orders'] = Order.objects.filter(status='shipped').count()
    extra_context['todays_orders'] = Order.objects.filter(created_at__date=date.today()).count()

    return _original_index(request, extra_context=extra_context)


admin.site.index = custom_index


# ——————————————————————————
# Delivery Calendar Views
def delivery_calendar_view(request):
    return TemplateResponse(request, "admin/delivery_calendar.html", {})


def delivery_events(request):
    events = []
    approved_requests = QuoteRequest.objects.filter(status='approved')
    for req in approved_requests:
        events.append({
            "title": f"{req.customer_name} — {req.delivery_address}",
            "start": str(req.preferred_date),
            "url": reverse("admin:quotes_quoterequest_change", args=[req.id])
        })
    return JsonResponse(events, safe=False)


# ——————————————————————————
# Enhanced Admin URLs
def get_admin_urls(urls):
    def custom_urls():
        return [
            path('delivery-calendar/', admin.site.admin_view(delivery_calendar_view), name='delivery_calendar'),
            path('delivery-events/', admin.site.admin_view(delivery_events), name='delivery_events'),
            path('generate-packing-slip/<int:order_id>/', admin.site.admin_view(generate_packing_slip),
                 name='generate_packing_slip'),
            # New delivery management URLs
            path('accept-delivery/<int:order_id>/', admin.site.admin_view(accept_delivery_view),
                 name='accept_delivery'),
            path('reject-delivery/<int:order_id>/', admin.site.admin_view(reject_delivery_view),
                 name='reject_delivery'),
            path('send-to-rb-transport/<int:order_id>/', admin.site.admin_view(send_to_rb_transport_view),
                 name='send_to_rb_transport'),
        ] + urls

    return custom_urls


admin.site.get_urls = get_admin_urls(admin.site.get_urls())



