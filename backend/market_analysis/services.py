from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import MarketPriceSnapshot


BANGLADESH_DIVISIONS = [
    'Barishal',
    'Chattogram',
    'Dhaka',
    'Khulna',
    'Mymensingh',
    'Rajshahi',
    'Rangpur',
    'Sylhet',
]

BANGLADESHI_FISH = [
    {'name': 'Rui', 'base_price': 330},
    {'name': 'Katla', 'base_price': 360},
    {'name': 'Hilsha', 'base_price': 1250},
    {'name': 'Pangasius', 'base_price': 190},
    {'name': 'Tilapia', 'base_price': 220},
    {'name': 'Shrimp', 'base_price': 780},
    {'name': 'Koi', 'base_price': 260},
    {'name': 'Pabda', 'base_price': 520},
]

DIVISION_PRICE_FACTORS = {
    'Barishal': 0.96,
    'Chattogram': 1.06,
    'Dhaka': 1.14,
    'Khulna': 1.02,
    'Mymensingh': 0.94,
    'Rajshahi': 0.98,
    'Rangpur': 0.92,
    'Sylhet': 1.03,
}

DEMAND_LEVELS = [
    MarketPriceSnapshot.DemandLevel.LOW,
    MarketPriceSnapshot.DemandLevel.MEDIUM,
    MarketPriceSnapshot.DemandLevel.HIGH,
]


def ensure_generated_market_data():
    if MarketPriceSnapshot.objects.exists():
        return False

    today = timezone.localdate()
    records = []

    for day_offset in range(7, -1, -1):
        date = today - timedelta(days=day_offset)
        for fish_index, fish in enumerate(BANGLADESHI_FISH):
            for division_index, division in enumerate(BANGLADESH_DIVISIONS):
                factor = DIVISION_PRICE_FACTORS[division]
                wave = ((fish_index * 5 + division_index * 3 + day_offset * 2) % 13) - 6
                trend = (7 - day_offset) * ((fish_index % 3) - 1) * 1.6
                price = max(80, fish['base_price'] * factor + wave * 3.5 + trend)
                demand = DEMAND_LEVELS[(fish_index + division_index + day_offset) % len(DEMAND_LEVELS)]
                records.append(MarketPriceSnapshot(
                    fish_name=fish['name'],
                    division=division,
                    recorded_date=date,
                    price_per_kg=Decimal(str(round(price, 2))),
                    demand_level=demand,
                ))

    with transaction.atomic():
        MarketPriceSnapshot.objects.bulk_create(records, ignore_conflicts=True)

    return True


def build_market_dashboard():
    generated = ensure_generated_market_data()
    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    records = list(
        MarketPriceSnapshot.objects
        .filter(recorded_date__gte=today - timedelta(days=7), recorded_date__lte=today)
        .order_by('fish_name', 'division', 'recorded_date')
    )

    grouped = defaultdict(list)
    for record in records:
        grouped[(record.fish_name, record.division)].append(record)

    rows = []
    today_prices = []
    high_demand_count = 0
    biggest_mover = None

    for (fish_name, division), group in sorted(grouped.items()):
        history = [record for record in group if record.recorded_date >= start_date]
        today_record = next((record for record in reversed(group) if record.recorded_date == today), group[-1])
        yesterday_record = next(
            (record for record in reversed(group) if record.recorded_date == today - timedelta(days=1)),
            None,
        )
        change_amount = Decimal('0.00')
        change_percent = Decimal('0.00')

        if yesterday_record:
            change_amount = today_record.price_per_kg - yesterday_record.price_per_kg
            if yesterday_record.price_per_kg:
                change_percent = (change_amount / yesterday_record.price_per_kg) * Decimal('100')

        direction = 'flat'
        if change_amount > 0:
            direction = 'up'
        elif change_amount < 0:
            direction = 'down'

        prediction_step = calculate_prediction_step(history)
        predictions = [
            {
                'date': (today + timedelta(days=index)).isoformat(),
                'predicted_price': round_decimal(
                    max(Decimal('80.00'), today_record.price_per_kg + prediction_step * index),
                ),
            }
            for index in range(1, 8)
        ]

        row = {
            'fish_name': fish_name,
            'division': division,
            'today_price': round_decimal(today_record.price_per_kg),
            'yesterday_price': round_decimal(yesterday_record.price_per_kg) if yesterday_record else None,
            'change_amount': round_decimal(change_amount),
            'change_percent': round_decimal(change_percent),
            'direction': direction,
            'demand_level': today_record.demand_level,
            'last_7_days': [
                {
                    'date': record.recorded_date.isoformat(),
                    'price': round_decimal(record.price_per_kg),
                    'demand_level': record.demand_level,
                }
                for record in history
            ],
            'next_7_days': predictions,
        }
        rows.append(row)
        today_prices.append(today_record.price_per_kg)

        if today_record.demand_level == MarketPriceSnapshot.DemandLevel.HIGH:
            high_demand_count += 1

        if biggest_mover is None or abs(change_percent) > abs(Decimal(str(biggest_mover['change_percent']))):
            biggest_mover = {
                'fish_name': fish_name,
                'division': division,
                'change_percent': round_decimal(change_percent),
                'direction': direction,
            }

    average_price = sum(today_prices, Decimal('0.00')) / len(today_prices) if today_prices else Decimal('0.00')

    return {
        'generated': generated,
        'currency': 'BDT',
        'unit': 'kg',
        'as_of_date': today.isoformat(),
        'divisions': BANGLADESH_DIVISIONS,
        'fish': [fish['name'] for fish in BANGLADESHI_FISH],
        'summary': {
            'market_points': len(rows),
            'average_price_today': round_decimal(average_price),
            'high_demand_count': high_demand_count,
            'biggest_mover': biggest_mover,
        },
        'records': rows,
    }


def calculate_prediction_step(history):
    if len(history) < 2:
        return Decimal('0.00')

    first_price = history[0].price_per_kg
    last_price = history[-1].price_per_kg
    return (last_price - first_price) / Decimal(len(history) - 1)


def round_decimal(value):
    return float(Decimal(value).quantize(Decimal('0.01')))
