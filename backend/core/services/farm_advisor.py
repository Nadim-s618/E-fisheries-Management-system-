import json
from datetime import date, datetime
from decimal import Decimal

from core.services.gemini import GeminiError, generate_json_response, is_gemini_configured
from feeding.models import FeedingRecommendation
from fish_health.models import HealthRecord
from stocks.models import FishStock
from water_quality.models import WaterQualityReading
from weather.models import WeatherReport


def get_farm_advice(pond):
    context = build_farm_context(pond)
    fallback = build_fallback_advice(context)

    if not is_gemini_configured():
        return fallback

    try:
        ai_advice = generate_json_response(build_farm_prompt(context), max_output_tokens=900)
    except (GeminiError, TypeError, ValueError):
        return fallback

    return {
        'source': 'gemini',
        'ai_enabled': True,
        'summary': str(ai_advice.get('summary') or fallback['summary']).strip(),
        'priority': str(ai_advice.get('priority') or fallback['priority']).strip(),
        'recommendations': normalize_list(ai_advice.get('recommendations')) or fallback['recommendations'],
        'risks': normalize_list(ai_advice.get('risks')) or fallback['risks'],
        'next_actions': normalize_list(ai_advice.get('next_actions')) or fallback['next_actions'],
        'context': context,
    }


def build_farm_context(pond):
    active_stocks = FishStock.objects.filter(
        pond=pond,
        status=FishStock.Status.ACTIVE,
        current_quantity__gt=0,
    )
    latest_water = (
        WaterQualityReading.objects
        .filter(pond=pond)
        .order_by('-created_at')
        .first()
    )
    latest_weather = (
        WeatherReport.objects
        .filter(pond=pond)
        .order_by('-observed_at', '-created_at')
        .first()
    )
    latest_feeding = (
        FeedingRecommendation.objects
        .filter(pond=pond)
        .order_by('-recommendation_date', '-created_at')
        .first()
    )
    latest_health = (
        HealthRecord.objects
        .filter(pond=pond)
        .order_by('-observed_at', '-created_at')
        .first()
    )

    return serialize({
        'pond': {
            'name': pond.name,
            'location': pond.location,
            'area_decimal': pond.area_decimal,
            'average_depth_ft': pond.average_depth_ft,
            'water_source': pond.water_source,
            'stocking_capacity': pond.stocking_capacity,
            'status': pond.status,
        },
        'stock': {
            'active_batches': active_stocks.count(),
            'current_quantity': sum(stock.current_quantity for stock in active_stocks),
            'species': sorted({stock.species for stock in active_stocks}),
        },
        'water_quality': snapshot_water(latest_water),
        'weather': snapshot_weather(latest_weather),
        'feeding': snapshot_feeding(latest_feeding),
        'fish_health': snapshot_health(latest_health),
    })


def snapshot_water(reading):
    if reading is None:
        return {}

    return {
        'overall_status': reading.overall_status,
        'temperature': reading.temperature,
        'ph': reading.ph,
        'dissolved_oxygen': reading.dissolved_oxygen,
        'ammonia': reading.ammonia,
        'nitrite': reading.nitrite,
        'nitrate': reading.nitrate,
        'turbidity': reading.turbidity,
        'water_level': reading.water_level,
        'created_at': reading.created_at,
    }


def snapshot_weather(report):
    if report is None:
        return {}

    return {
        'fish_weather_risk': report.fish_weather_risk,
        'disease_risk': report.disease_risk,
        'air_temperature': report.air_temperature,
        'rainfall_probability': report.rainfall_probability,
        'rainfall_mm': report.rainfall_mm,
        'observed_at': report.observed_at,
    }


def snapshot_feeding(recommendation):
    if recommendation is None:
        return {}

    return {
        'recommendation_date': recommendation.recommendation_date,
        'recommended_feed_kg': recommendation.recommended_feed_kg,
        'feed_type': recommendation.feed_type,
        'meals': recommendation.meals,
        'status': recommendation.status,
        'reasons': recommendation.reasons,
        'ai_advice': (recommendation.input_summary or {}).get('ai_advice', {}),
    }


def snapshot_health(record):
    if record is None:
        return {}

    return {
        'observed_at': record.observed_at,
        'species': record.species,
        'symptoms': record.symptoms,
        'affected_count': record.affected_count,
        'mortality_count': record.mortality_count,
        'severity': record.severity,
        'status': record.status,
        'recommendation': record.ai_recommendation,
    }


def build_fallback_advice(context):
    risks = []
    recommendations = []

    water_status = context.get('water_quality', {}).get('overall_status')
    if not water_status:
        risks.append('Water quality data is missing.')
        recommendations.append('Record a fresh water quality reading before changing feed or stocking decisions.')
    elif water_status != 'Good':
        risks.append(f'Water quality is {water_status}.')
        recommendations.append('Prioritize water correction before increasing feed or handling fish.')

    health_severity = context.get('fish_health', {}).get('severity')
    if health_severity in {'High', 'Critical'}:
        risks.append(f'Latest fish health severity is {health_severity}.')
        recommendations.append('Monitor affected fish closely and confirm diagnosis before treatment.')

    if not context.get('stock', {}).get('current_quantity'):
        risks.append('No active stock quantity is available.')
        recommendations.append('Update stock records so future recommendations can calculate biomass accurately.')

    if not recommendations:
        recommendations.append('Maintain routine monitoring and keep feeding, water quality, and health records current.')

    return {
        'source': 'fallback',
        'ai_enabled': False,
        'summary': 'General pond advice generated from available farm records.',
        'priority': 'Normal' if not risks else 'Attention',
        'recommendations': recommendations,
        'risks': risks,
        'next_actions': [
            'Review water quality, feeding, and fish health records daily.',
            'Refresh missing records before relying on long-term planning decisions.',
        ],
        'context': context,
    }


def build_farm_prompt(context):
    return (
        'You are an aquaculture farm advisor. Use English only. '
        'Use only the provided pond, stock, water quality, weather, feeding, and health context. '
        'Return JSON with keys: summary, priority, recommendations, risks, next_actions. '
        'recommendations, risks, and next_actions must be arrays of concise practical strings. '
        'Do not claim certainty when data is missing. '
        f'Data: {json.dumps(context)}'
    )


def normalize_list(values):
    if not isinstance(values, list):
        return []

    return [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]


def serialize(value):
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value
