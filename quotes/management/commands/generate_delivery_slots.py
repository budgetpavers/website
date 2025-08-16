from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from quotes.models import DeliveryTemplate, DeliverySlot


class Command(BaseCommand):
    help = 'Generate delivery slots for the next week based on templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days ahead to generate slots (default: 7)'
        )
        parser.add_argument(
            '--clean-old',
            action='store_true',
            help='Remove old auto-generated slots before creating new ones'
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        clean_old = options['clean_old']

        self.stdout.write(f"🚛 Generating delivery slots for the next {days_ahead} days...")

        # Clean old slots if requested
        if clean_old:
            old_slots_count = DeliverySlot.objects.filter(
                is_auto_generated=True,
                date__lt=date.today()
            ).count()

            if old_slots_count > 0:
                DeliverySlot.objects.filter(
                    is_auto_generated=True,
                    date__lt=date.today()
                ).delete()
                self.stdout.write(f"🗑️  Cleaned up {old_slots_count} old auto-generated slots")

        # Get active templates
        templates = DeliveryTemplate.objects.filter(is_active=True)

        if not templates.exists():
            self.stdout.write(
                self.style.WARNING("⚠️  No active delivery templates found. Create templates first!")
            )
            return

        created_count = 0
        skipped_count = 0

        # Generate slots for each day
        start_date = date.today() + timedelta(days=1)  # Start from tomorrow

        for day_offset in range(days_ahead):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday

            # Find templates for this day of week
            day_templates = templates.filter(day_of_week=day_of_week)

            for template in day_templates:
                # Check if this date is excluded
                excluded_dates = template.get_excluded_dates()
                if current_date in excluded_dates:
                    self.stdout.write(f"⏭️  Skipping {current_date} - excluded date for template '{template.name}'")
                    skipped_count += 1
                    continue

                # Check if slot already exists (avoid duplicates)
                existing_slot = DeliverySlot.objects.filter(
                    date=current_date,
                    time_slot=template.time_slot,
                    delivery_type=template.delivery_type
                ).first()

                if existing_slot:
                    self.stdout.write(
                        f"⏭️  Slot exists: {current_date} {template.time_slot} ({template.delivery_type})")
                    skipped_count += 1
                    continue

                # Create new slot
                slot = DeliverySlot.objects.create(
                    date=current_date,
                    time_slot=template.time_slot,
                    capacity=template.capacity,
                    delivery_type=template.delivery_type,
                    notes=template.notes,
                    template=template,
                    is_auto_generated=True,
                    created_by='Auto-generated'
                )

                self.stdout.write(f"✅ Created: {slot}")
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Delivery slot generation complete!\n"
                f"   Created: {created_count} new slots\n"
                f"   Skipped: {skipped_count} existing/excluded slots"
            )
        )

        # Show summary of upcoming week
        upcoming_slots = DeliverySlot.objects.filter(
            date__gte=date.today(),
            date__lte=date.today() + timedelta(days=7),
            is_available=True
        ).order_by('date', 'time_slot')

        self.stdout.write(f"\n📅 Upcoming week summary ({upcoming_slots.count()} available slots):")

        for slot in upcoming_slots:
            availability = f"{slot.available_capacity}/{slot.capacity} available"
            self.stdout.write(f"   {slot.date} {slot.time_slot} - {availability}")