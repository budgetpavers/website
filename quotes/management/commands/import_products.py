import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from quotes.models import Product


class Command(BaseCommand):
    help = 'Import products from Excel files'

    def handle(self, *args, **options):
        self.stdout.write('Starting product import...')

        # Define all Excel files with their categories
        excel_files = [
            {
                'file': 'SC Sleepers Pricelist.xlsx',
                'category': 'Concrete Sleepers - Silvercrete'
            },
            {
                'file': 'SC UFP+Cribs Pricelist.xlsx',
                'category': 'Under Fence Plinths - Silvercrete'
            },
            {
                'file': 'OS Sleepers Pricelist.xlsx',
                'category': 'Concrete Sleepers - Outback'
            },
            {
                'file': 'OS UFP+Cribs Pricelist.xlsx',
                'category': 'Under Fence Plinths - Outback'
            },
            {
                'file': 'OS Accessories Pricelist.xlsx',
                'category': 'Accessories'
            },
            {
                'file': 'Steel Pricelist.xlsx',
                'category': 'Steel Posts & Hardware'
            }
        ]

        total_imported = 0
        total_updated = 0

        # Process each file
        for file_info in excel_files:
            file_path = os.path.join(settings.BASE_DIR, file_info['file'])

            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'File not found: {file_info["file"]}')
                )
                continue

            self.stdout.write(f'Processing {file_info["file"]}...')

            # Import products from this file
            imported, updated = self.import_excel_file(file_path, file_info['category'])
            total_imported += imported
            total_updated += updated

        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete! Added {total_imported} new products, updated {total_updated} existing products.'
            )
        )

    def import_excel_file(self, file_path, category):
        """Import products from a single Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            imported_count = 0
            updated_count = 0

            self.stdout.write(f'Found {len(df)} rows in {os.path.basename(file_path)}')

            for index, row in df.iterrows():
                # Skip header row or rows with missing essential data
                if (pd.isna(row.get('Item Code')) or
                        pd.isna(row.get('Item (50 Characters) (searchable)')) or
                        str(row.get('Item Code')).strip() == 'Item Code'):
                    continue

                # Extract and clean data
                sku = str(row['Item Code']).strip()
                name = str(row['Item (50 Characters) (searchable)']).strip()
                description = str(row.get('Description (2000 Characters) (shows on invoices to customers)', '')).strip()

                # FIXED: Use EXCLUDING GST price instead of INCLUDING GST
                price_inc_gst = self.safe_float(row.get('Sale Price (Including GST)', 0))
                if price_inc_gst > 0:
                    price_ex_gst = price_inc_gst / 1.10  # Remove 10% GST
                else:
                    # Try excluding GST column if available
                    price_ex_gst = self.safe_float(row.get('Sale Price (Excluding GST)', 0))

                weight = self.safe_float(row.get('Weight (kg)', 0))
                color = str(row.get('Colour', '')).strip()

                # FIXED: Move wheel stops to accessories category
                final_category = category
                if 'wheel stop' in name.lower() and 'fixing' not in name.lower():
                    final_category = 'Accessories'

                # Skip if essential data is missing
                if not sku or not name:
                    continue

                try:
                    # Check if product already exists
                    existing_product = Product.objects.filter(sku=sku).first()

                    if existing_product:
                        # Update existing product
                        existing_product.name = name
                        existing_product.description = description
                        existing_product.price = price_ex_gst  # FIXED: Now using ex GST
                        existing_product.weight = weight
                        existing_product.color = color
                        existing_product.category = final_category
                        existing_product.is_active = True
                        existing_product.save()

                        updated_count += 1
                        self.stdout.write(f'Updated: {name} (SKU: {sku}, ${price_ex_gst:.2f} ex GST)')
                    else:
                        # Create new product
                        Product.objects.create(
                            sku=sku,
                            name=name,
                            description=description,
                            price=price_ex_gst,  # FIXED: Now using ex GST
                            weight=weight,
                            color=color,
                            category=final_category,
                            is_active=True
                        )

                        imported_count += 1
                        self.stdout.write(f'Added: {name} (SKU: {sku}, ${price_ex_gst:.2f} ex GST)')

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing product {sku}: {str(e)}')
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {final_category}: {imported_count} new, {updated_count} updated'
                )
            )
            return imported_count, updated_count

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ERROR importing {file_path}: {str(e)}')
            )
            return 0, 0

    def safe_float(self, value):
        """Safely convert value to float, return 0 if conversion fails"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0