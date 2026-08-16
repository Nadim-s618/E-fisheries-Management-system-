from decimal import Decimal

from django.db.models import Avg

from core.models import Notification
from market_analysis.models import MarketPriceSnapshot
from market_analysis.services import ensure_generated_market_data, round_decimal


DIVISION_ALIASES = {
    'barishal': 'Barishal',
    'chattogram': 'Chattogram',
    'chittagong': 'Chattogram',
    'dhaka': 'Dhaka',
    'khulna': 'Khulna',
    'mymensingh': 'Mymensingh',
    'rajshahi': 'Rajshahi',
    'rangpur': 'Rangpur',
    'sylhet': 'Sylhet',
}


def get_or_create_market_profile(user):
    from .models import MarketProfile

    profile, _ = MarketProfile.objects.get_or_create(user=user)
    return profile


def notify_new_market_order(order):
    """Observer callback for a newly created market order."""
    Notification.objects.create(
        user=order.listing.seller,
        parameter='New fish store order',
        current_value=f'{order.quantity_kg:g} kg · BDT {order.total_price:,.2f}',
        reason=(
            f'{order.buyer_full_name} ordered {order.listing.title}. '
            f'Tracking code: {order.transaction_code}.'
        ),
        priority=Notification.Priority.MEDIUM,
    )


def infer_division(location):
    text = (location or '').lower()
    for key, division in DIVISION_ALIASES.items():
        if key in text:
            return division
    return ''


def recommend_price(species, location='', quantity_kg=None):
    ensure_generated_market_data()
    species = (species or '').strip()
    division = infer_division(location)

    snapshots = MarketPriceSnapshot.objects.all()
    if species:
        snapshots = snapshots.filter(fish_name__iexact=species)
    if division:
        snapshots = snapshots.filter(division=division)

    latest_date = snapshots.order_by('-recorded_date').values_list('recorded_date', flat=True).first()
    if latest_date:
        snapshots = snapshots.filter(recorded_date=latest_date)

    average = snapshots.aggregate(value=Avg('price_per_kg'))['value']
    if average is None and species:
        average = (
            MarketPriceSnapshot.objects
            .filter(fish_name__iexact=species)
            .order_by('-recorded_date')
            .values_list('price_per_kg', flat=True)
            .first()
        )
    if average is None:
        average = (
            MarketPriceSnapshot.objects
            .order_by('-recorded_date')
            .values_list('price_per_kg', flat=True)
            .first()
        )

    base_price = Decimal(str(average or 250))
    quantity = Decimal(str(quantity_kg or 0))
    quantity_adjustment = Decimal('1.00')

    if quantity >= Decimal('500'):
        quantity_adjustment = Decimal('0.96')
    elif quantity >= Decimal('200'):
        quantity_adjustment = Decimal('0.98')
    elif Decimal('0') < quantity <= Decimal('25'):
        quantity_adjustment = Decimal('1.04')

    suggested = max(Decimal('1.00'), base_price * quantity_adjustment)

    return {
        'species': species,
        'division': division or None,
        'currency': 'BDT',
        'unit': 'kg',
        'suggested_price': round_decimal(suggested),
        'low_price': round_decimal(suggested * Decimal('0.94')),
        'high_price': round_decimal(suggested * Decimal('1.08')),
        'basis': 'latest_market_snapshot',
    }
