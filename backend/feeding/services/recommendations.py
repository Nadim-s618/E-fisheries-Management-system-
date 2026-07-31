from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from growth.models import GrowthRecord
from stocks.models import FishStock
from water_quality.models import WaterQualityReading
from weather.models import WeatherReport

from feeding.models import FeedingRecommendation, FeedingSession
from feeding.services.notifications import create_feeding_notification


DEFAULT_FEED_TYPE = 'Floating Feed 32%'
DEFAULT_PRICE_PER_KG = Decimal('4.50')
DEFAULT_MEAL_TIMES = ['08:00', '16:30']
REDUCED_MEAL_TIMES = ['09:00']


def kg(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_or_create_draft_recommendation(pond, recommendation_date=None, force_new=False):
    recommendation_date = recommendation_date or timezone.localdate()

    if not force_new:
        existing = FeedingRecommendation.objects.filter(
            pond=pond,
            recommendation_date=recommendation_date,
            status=FeedingRecommendation.Status.DRAFT,
        ).order_by('-created_at').first()

        if existing:
            return existing, False

    payload = build_recommendation_payload(pond, recommendation_date)
    FeedingRecommendation.objects.filter(
        pond=pond,
        recommendation_date=recommendation_date,
        status=FeedingRecommendation.Status.DRAFT,
    ).update(status=FeedingRecommendation.Status.SUPERSEDED)

    recommendation = FeedingRecommendation.objects.create(pond=pond, **payload)
    create_feeding_notification(
        pond=pond,
        parameter='Feeding recommendation',
        current_value=f"{recommendation.recommended_feed_kg} kg",
        reason=f'New feed recommendation is ready for {pond.name}.',
    )
    return recommendation, True


def build_recommendation_payload(pond, recommendation_date):
    stock_summary = get_stock_summary(pond)
    water_summary = get_water_summary(pond)
    weather_summary = get_weather_summary(pond)
    history_summary = get_history_summary(pond)

    base_feed = stock_summary['biomass_kg'] * stock_summary['feeding_rate']
    multiplier = water_summary['multiplier'] * weather_summary['multiplier']
    recommended_feed = base_feed * multiplier

    if history_summary['recent_average_kg'] is not None and recommended_feed > 0:
        recent_average = history_summary['recent_average_kg']
        lower_bound = recent_average * Decimal('0.85')
        upper_bound = recent_average * Decimal('1.15')
        recommended_feed = min(max(recommended_feed, lower_bound), upper_bound)

    if recommended_feed <= 0:
        recommended_feed = Decimal('1.00')

    recommended_feed = kg(recommended_feed)
    meals = 1 if multiplier < Decimal('0.70') else 2
    meal_times = REDUCED_MEAL_TIMES if meals == 1 else DEFAULT_MEAL_TIMES
    schedule = build_schedule(recommendation_date, recommended_feed, meal_times)
    price_per_kg = DEFAULT_PRICE_PER_KG

    return {
        'recommendation_date': recommendation_date,
        'recommended_feed_kg': recommended_feed,
        'feed_type': DEFAULT_FEED_TYPE,
        'price_per_kg': price_per_kg,
        'estimated_cost': kg(recommended_feed * price_per_kg),
        'meals': meals,
        'schedule': schedule,
        'reasons': build_reasons(water_summary, weather_summary, stock_summary),
        'input_summary': {
            'stock': serialize_decimals(stock_summary),
            'water_quality': serialize_decimals(water_summary),
            'weather': serialize_decimals(weather_summary),
            'feeding_history': serialize_decimals(history_summary),
        },
    }


def get_stock_summary(pond):
    stocks = FishStock.objects.filter(
        pond=pond,
        status=FishStock.Status.ACTIVE,
        current_quantity__gt=0,
    )
    latest_records = {}
    for record in GrowthRecord.objects.filter(stock__in=stocks).order_by(
        'stock_id',
        '-recorded_date',
        '-id',
    ):
        latest_records.setdefault(record.stock_id, record)

    total_biomass = Decimal('0')
    weighted_rate = Decimal('0')
    total_quantity = 0

    for stock in stocks:
        latest_record = latest_records.get(stock.id)
        source_weight = latest_record.average_weight_g if latest_record else stock.initial_average_weight_g
        average_weight = Decimal(str(source_weight))
        biomass = (Decimal(stock.current_quantity) * average_weight) / Decimal('1000')
        feeding_rate = get_feeding_rate(average_weight)
        total_biomass += biomass
        weighted_rate += feeding_rate * biomass
        total_quantity += stock.current_quantity

    rate = weighted_rate / total_biomass if total_biomass > 0 else Decimal('0.025')

    return {
        'active_batches': stocks.count(),
        'current_quantity': total_quantity,
        'biomass_kg': kg(total_biomass),
        'feeding_rate': rate,
    }


def get_feeding_rate(average_weight_g):
    if average_weight_g < 50:
        return Decimal('0.040')
    if average_weight_g < 150:
        return Decimal('0.030')
    if average_weight_g < 500:
        return Decimal('0.025')
    return Decimal('0.018')


def get_water_summary(pond):
    reading = WaterQualityReading.objects.filter(pond=pond).order_by('-created_at').first()

    if reading is None:
        return {
            'status': 'No data',
            'multiplier': Decimal('0.90'),
            'reason': 'No recent water quality reading',
        }

    status = reading.overall_status
    multiplier = {
        WaterQualityReading.OverallStatus.GOOD: Decimal('1.00'),
        WaterQualityReading.OverallStatus.WARNING: Decimal('0.75'),
        WaterQualityReading.OverallStatus.DANGER: Decimal('0.35'),
    }.get(status, Decimal('0.90'))

    return {
        'status': status,
        'multiplier': multiplier,
        'reason': f'Water quality {status.lower()}',
        'reading_id': reading.id,
        'created_at': reading.created_at.isoformat(),
    }


def get_weather_summary(pond):
    report = WeatherReport.objects.filter(pond=pond).order_by('-observed_at', '-created_at').first()

    if report is None:
        return {
            'risk': 'No data',
            'multiplier': Decimal('0.95'),
            'reason': 'No recent weather report',
        }

    multiplier = {
        WeatherReport.RiskLevel.LOW: Decimal('1.00'),
        WeatherReport.RiskLevel.MODERATE: Decimal('0.80'),
        WeatherReport.RiskLevel.HIGH: Decimal('0.50'),
    }.get(report.fish_weather_risk, Decimal('0.95'))

    return {
        'risk': report.fish_weather_risk,
        'multiplier': multiplier,
        'reason': f'Weather risk {report.fish_weather_risk.lower()}',
        'report_id': report.id,
        'observed_at': report.observed_at.isoformat(),
        'rainfall_probability': Decimal(str(report.rainfall_probability)),
        'air_temperature': Decimal(str(report.air_temperature)),
    }


def get_history_summary(pond):
    since = timezone.now() - timedelta(days=7)
    rows = FeedingSession.objects.filter(
        pond=pond,
        status=FeedingSession.Status.COMPLETED,
        completed_at__gte=since,
    )
    total = rows.aggregate(total=Sum('actual_feed_kg'))['total']
    days = rows.dates('completed_at', 'day').count()

    if not total or not days:
        return {
            'recent_average_kg': None,
            'completed_sessions_7d': rows.count(),
        }

    return {
        'recent_average_kg': kg(Decimal(total) / Decimal(days)),
        'completed_sessions_7d': rows.count(),
    }


def build_reasons(water_summary, weather_summary, stock_summary):
    reasons = []

    if water_summary['status'] == 'Good':
        reasons.append('Water quality optimal')
    elif water_summary['status'] == 'No data':
        reasons.append('Water quality data missing')
    else:
        reasons.append(water_summary['reason'])

    if weather_summary['risk'] == 'Low':
        reasons.append('Good weather')
    elif weather_summary['risk'] == 'No data':
        reasons.append('Weather data missing')
    else:
        reasons.append(weather_summary['reason'])

    if stock_summary['current_quantity'] > 0:
        reasons.append('Healthy fish')
    else:
        reasons.append('No active fish stock found')

    return reasons


def build_schedule(recommendation_date, total_feed_kg, meal_times):
    meal_count = len(meal_times)
    base_amount = kg(total_feed_kg / Decimal(meal_count))
    schedule = []
    allocated = Decimal('0')

    for index, meal_time in enumerate(meal_times, start=1):
        if index == meal_count:
            amount = kg(total_feed_kg - allocated)
        else:
            amount = base_amount
            allocated += amount

        schedule.append({
            'meal_number': index,
            'time': meal_time,
            'label': format_time_label(meal_time),
            'feed_kg': str(amount),
        })

    return schedule


def create_sessions(recommendation):
    getattr(recommendation, '_prefetched_objects_cache', {}).pop('sessions', None)

    if recommendation.sessions.exists():
        return list(recommendation.sessions.all())

    sessions = []
    for item in recommendation.schedule:
        sessions.append(FeedingSession.objects.create(
            recommendation=recommendation,
            pond=recommendation.pond,
            meal_number=item['meal_number'],
            scheduled_at=make_scheduled_at(recommendation.recommendation_date, item['time']),
            planned_feed_kg=item['feed_kg'],
        ))

    getattr(recommendation, '_prefetched_objects_cache', {}).pop('sessions', None)
    return sessions


def make_scheduled_at(recommendation_date, meal_time):
    hour, minute = [int(part) for part in meal_time.split(':', 1)]
    value = datetime.combine(recommendation_date, time(hour=hour, minute=minute))

    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())

    return value


def format_time_label(meal_time):
    hour, minute = [int(part) for part in meal_time.split(':', 1)]
    return datetime(2000, 1, 1, hour, minute).strftime('%I:%M %p').lstrip('0')


def serialize_decimals(value):
    if isinstance(value, dict):
        return {key: serialize_decimals(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return str(kg(value))
    return value


def update_recommendation_from_edit(recommendation, data):
    feed_kg = kg(data.get('recommended_feed_kg', recommendation.recommended_feed_kg))
    price_per_kg = kg(data.get('price_per_kg', recommendation.price_per_kg))
    meals = int(data.get('meals', recommendation.meals))
    meal_times = data.get('meal_times') or [item['time'] for item in recommendation.schedule]

    if len(meal_times) != meals:
        fallback_times = DEFAULT_MEAL_TIMES + ['12:30', '18:30']
        meal_times = fallback_times[:meals] if meals > 1 else REDUCED_MEAL_TIMES

    recommendation.recommended_feed_kg = feed_kg
    recommendation.feed_type = data.get('feed_type', recommendation.feed_type)
    recommendation.price_per_kg = price_per_kg
    recommendation.estimated_cost = kg(feed_kg * price_per_kg)
    recommendation.meals = meals
    recommendation.schedule = build_schedule(recommendation.recommendation_date, feed_kg, meal_times)
    recommendation.status = FeedingRecommendation.Status.EDITED
    recommendation.save()
    recommendation.sessions.all().delete()
    create_sessions(recommendation)

    return recommendation
