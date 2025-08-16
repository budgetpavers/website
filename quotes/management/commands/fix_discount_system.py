from django.core.management.base import BaseCommand
from django.db import transaction
from quotes.models import DiscountCode, DiscountableProduct, Product


class Command(BaseCommand):
    help = 'Migrate discount system from products_data.py to database Product model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write('🔍 Analyzing discount system...')

        # Step 1: Check existing discount codes
        discount_codes = DiscountCode.objects.all()
        self.stdout.write(f'Found {discount_codes.count()} discount codes')

        # Step 2: Check if we have the new fields
        try:
            # Test if the new fields exist
            sample_discount = discount_codes.first()
            if sample_discount:
                hasattr(sample_discount, 'applicable_categories')
                self.stdout.write('✅ New discount fields detected')
        except:
            self.stdout.write(self.style.ERROR('❌ New discount fields not found. Please run migrations first.'))
            return

        # Step 3: Check legacy DiscountableProduct usage
        legacy_products = DiscountableProduct.objects.all()
        self.stdout.write(f'Found {legacy_products.count()} legacy discountable products')

        # Step 4: Find discounts using legacy system
        problematic_discounts = []
        for discount in discount_codes:
            if discount.applicable_products.count() > 0 or discount.exclude_products.count() > 0:
                # Check if these are legacy DiscountableProduct or new Product
                first_applicable = discount.applicable_products.first()
                if first_applicable and isinstance(first_applicable, DiscountableProduct):
                    problematic_discounts.append(discount)

        self.stdout.write(f'Found {len(problematic_discounts)} discounts using legacy product system')

        # Step 5: Migration plan
        database_products = Product.objects.filter(is_active=True)
        self.stdout.write(f'Available database products: {database_products.count()}')

        if not dry_run:
            with transaction.atomic():
                # Migrate each problematic discount
                for discount in problematic_discounts:
                    self.migrate_discount_products(discount)

                self.stdout.write(self.style.SUCCESS('✅ Migration completed'))
        else:
            for discount in problematic_discounts:
                self.show_migration_plan(discount)

    def migrate_discount_products(self, discount):
        """Migrate a single discount from legacy to new system"""
        self.stdout.write(f'🔄 Migrating discount: {discount.code}')

        # Try to map legacy products to database products
        mapped_applicable = []
        mapped_exclude = []

        # Map applicable products
        for legacy_product in discount.applicable_products.all():
            db_product = self.find_matching_product(legacy_product)
            if db_product:
                mapped_applicable.append(db_product)
                self.stdout.write(f'  ✅ Mapped applicable: {legacy_product.name} → {db_product.name}')
            else:
                self.stdout.write(f'  ❌ Could not map: {legacy_product.name}')

        # Map exclude products
        for legacy_product in discount.exclude_products.all():
            db_product = self.find_matching_product(legacy_product)
            if db_product:
                mapped_exclude.append(db_product)
                self.stdout.write(f'  ✅ Mapped exclude: {legacy_product.name} → {db_product.name}')
            else:
                self.stdout.write(f'  ❌ Could not map: {legacy_product.name}')

        # Clear old relationships and set new ones
        discount.applicable_products.clear()
        discount.exclude_products.clear()

        # Set new relationships
        for product in mapped_applicable:
            discount.applicable_products.add(product)

        for product in mapped_exclude:
            discount.exclude_products.add(product)

        # Set category-based restrictions as fallback
        if not mapped_applicable and not mapped_exclude:
            # Convert to category-based restrictions
            categories = set()
            for legacy_product in discount.applicable_products.all():
                if legacy_product.category:
                    categories.add(legacy_product.category)

            if categories:
                discount.applicable_categories = ','.join(categories)
                discount.save()
                self.stdout.write(f'  📂 Set category restrictions: {discount.applicable_categories}')

    def find_matching_product(self, legacy_product):
        """Find matching Product in database for legacy DiscountableProduct"""

        # Try exact name match first
        exact_match = Product.objects.filter(
            name__iexact=legacy_product.name,
            is_active=True
        ).first()
        if exact_match:
            return exact_match

        # Try partial name match
        name_words = legacy_product.name.split()[:3]  # First 3 words
        for word in name_words:
            if len(word) > 3:  # Avoid short words
                matches = Product.objects.filter(
                    name__icontains=word,
                    is_active=True
                )
                if matches.count() == 1:
                    return matches.first()

        # Try category + first word
        if legacy_product.category:
            first_word = legacy_product.name.split()[0]
            matches = Product.objects.filter(
                category__icontains=legacy_product.category,
                name__icontains=first_word,
                is_active=True
            )
            if matches.count() == 1:
                return matches.first()

        return None

    def show_migration_plan(self, discount):
        """Show what would be migrated for this discount"""
        self.stdout.write(f'📋 Migration plan for: {discount.code}')

        applicable_count = discount.applicable_products.count()
        exclude_count = discount.exclude_products.count()

        self.stdout.write(f'  - {applicable_count} applicable products to migrate')
        self.stdout.write(f'  - {exclude_count} exclude products to migrate')

        # Show sample mappings
        for legacy_product in discount.applicable_products.all()[:3]:
            db_product = self.find_matching_product(legacy_product)
            if db_product:
                self.stdout.write(f'    ✅ {legacy_product.name} → {db_product.name}')
            else:
                self.stdout.write(f'    ❌ {legacy_product.name} → NOT FOUND')

        if applicable_count > 3:
            self.stdout.write(f'    ... and {applicable_count - 3} more')