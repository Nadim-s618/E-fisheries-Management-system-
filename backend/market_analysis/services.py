from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
import json

from django.db import transaction
from django.utils import timezone

from core.services.gemini import GeminiError, generate_json_response, is_gemini_configured

from .models import MarketPriceSnapshot


SOURCE_GEMINI = 'Gemini AI'
SOURCE_SAMPLE = 'Generated sample'
SOURCE_EXISTING = 'Existing snapshots'

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
    return ensure_market_data()['generated']


def ensure_market_data(force_refresh=False):
    if not force_refresh and MarketPriceSnapshot.objects.exists():
        return {
            'generated': False,
            'source': get_latest_source() or SOURCE_EXISTING,
        }

    today = timezone.localdate()
    records = []
    source = SOURCE_SAMPLE

    if is_gemini_configured():
        try:
            records = build_gemini_market_records(today)
            source = SOURCE_GEMINI
        except (
            GeminiError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            ArithmeticError,
        ):
            records = []

    if not records:
        records = build_sample_market_records(today, source=SOURCE_SAMPLE)
        source = SOURCE_SAMPLE

    with transaction.atomic():
        for record in records:
            MarketPriceSnapshot.objects.update_or_create(
                fish_name=record.fish_name,
                division=record.division,
                recorded_date=record.recorded_date,
                defaults={
                    'price_per_kg': record.price_per_kg,
                    'demand_level': record.demand_level,
                    'source': record.source,
                },
            )

    return {
        'generated': True,
        'source': source,
    }


def build_sample_market_records(today, source=SOURCE_SAMPLE):
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
                    source=source,
                ))

    return records


def build_gemini_market_records(today):
    response = generate_json_response(
        build_market_generation_prompt(today),
        temperature=0.35,
        max_output_tokens=12000,
    )
    rows = response.get('records')
    if not isinstance(rows, list):
        raise ValueError('Gemini market price response must contain a records list.')

    date_values = [today - timedelta(days=day_offset) for day_offset in range(7, -1, -1)]
    expected_pairs = {
        (fish['name'], division)
        for fish in BANGLADESHI_FISH
        for division in BANGLADESH_DIVISIONS
    }
    normalized_by_pair = {}

    for row in rows:
        fish_name = normalize_choice(row.get('fish_name'), [fish['name'] for fish in BANGLADESHI_FISH])
        division = normalize_choice(row.get('division'), BANGLADESH_DIVISIONS)
        prices = row.get('prices')
        demand_levels = row.get('demand_levels')

        if fish_name is None or division is None:
            continue
        if not isinstance(prices, list) or len(prices) != len(date_values):
            continue
        if not isinstance(demand_levels, list) or len(demand_levels) != len(date_values):
            continue

        normalized_prices = [normalize_price(price) for price in prices]
        normalized_demands = [normalize_demand_level(level) for level in demand_levels]
        normalized_by_pair[(fish_name, division)] = (normalized_prices, normalized_demands)

    missing_pairs = expected_pairs - set(normalized_by_pair)
    if missing_pairs:
        raise ValueError('Gemini market price response is missing fish/division combinations.')

    records = []
    for fish_name, division in sorted(expected_pairs):
        prices, demand_levels = normalized_by_pair[(fish_name, division)]
        for index, date in enumerate(date_values):
            records.append(MarketPriceSnapshot(
                fish_name=fish_name,
                division=division,
                recorded_date=date,
                price_per_kg=prices[index],
                demand_level=demand_levels[index],
                source=SOURCE_GEMINI,
            ))

    return records


def build_market_generation_prompt(today):
    fish_names = [fish['name'] for fish in BANGLADESHI_FISH]
    date_values = [
        (today - timedelta(days=day_offset)).isoformat()
        for day_offset in range(7, -1, -1)
    ]
    prompt_data = {
        'country': 'Bangladesh',
        'currency': 'BDT',
        'unit': 'kg',
        'dates': date_values,
        'fish': fish_names,
        'divisions': BANGLADESH_DIVISIONS,
        'base_price_reference': BANGLADESHI_FISH,
    }

    return (
        'You generate plausible aquaculture market price estimates for a fisheries dashboard. '
        'Use English only. Do not claim these are live, verified, or official prices. '
        'Generate realistic BDT per kg prices for each fish and Bangladesh division, using regional demand, '
        'urban transport cost, seasonal supply, and short weekly movement. '
        'Return JSON only with one top-level key named records. '
        'records must contain exactly one item for every fish/division pair. '
        'Each item must contain fish_name, division, prices, and demand_levels. '
        'prices must be 8 positive numbers ordered by the supplied dates. '
        'demand_levels must be 8 strings, each Low, Medium, or High, ordered by the supplied dates. '
        f'Data: {json.dumps(prompt_data)}'
    )


def normalize_choice(value, choices):
    text = str(value or '').strip().lower()
    lookup = {choice.lower(): choice for choice in choices}
    return lookup.get(text)


def normalize_price(value):
    price = Decimal(str(value)).quantize(Decimal('0.01'))
    if price < Decimal('80.00') or price > Decimal('5000.00'):
        raise ValueError('Gemini returned an unrealistic market price.')
    return price


def normalize_demand_level(value):
    text = str(value or '').strip().lower()
    if text == 'low':
        return MarketPriceSnapshot.DemandLevel.LOW
    if text == 'medium':
        return MarketPriceSnapshot.DemandLevel.MEDIUM
    if text == 'high':
        return MarketPriceSnapshot.DemandLevel.HIGH
    raise ValueError('Gemini returned an invalid demand level.')


def get_latest_source():
    return (
        MarketPriceSnapshot.objects
        .order_by('-recorded_date', '-updated_at')
        .values_list('source', flat=True)
        .first()
    )


def build_market_dashboard(force_refresh=False):
    generation = ensure_market_data(force_refresh=force_refresh)
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
            'source': today_record.source,
            'last_7_days': [
                {
                    'date': record.recorded_date.isoformat(),
                    'price': round_decimal(record.price_per_kg),
                    'demand_level': record.demand_level,
                    'source': record.source,
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
        'generated': generation['generated'],
        'price_source': generation['source'],
        'ai_enabled': generation['source'] == SOURCE_GEMINI,
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
