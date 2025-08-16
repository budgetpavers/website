from django.conf import settings

def stripe_context(request):
    """Make Stripe publishable key available in all templates"""
    return {
        'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    }