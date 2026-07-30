from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from .analysis import analyse_weather, parse_observed_at
from .notification_service import create_weather_notifications
from .openweather import SOURCE_NAME, SOURCE_URL, WeatherServiceError, fetch_forecast, geocode_location
from ..models import WeatherReport


def latest_weather_report(pond):
    return WeatherReport.objects.filter(pond=pond).first()


def get_or_refresh_weather_report(pond, force_refresh=False):
    latest_report = latest_weather_report(pond)

    if latest_report and not force_refresh and is_report_fresh(latest_report):
        return latest_report, False, None

    try:
        return create_weather_report(pond), False, None
    except WeatherServiceError as exc:
        if latest_report:
            return latest_report, True, str(exc)
        raise


def is_report_fresh(report):
    cache_minutes = getattr(settings, 'WEATHER_REPORT_CACHE_MINUTES', 30)
    age = timezone.now() - report.updated_at
    return age.total_seconds() < cache_minutes * 60


def create_weather_report(pond):
    location = geocode_location(pond.location, fallback_terms=[pond.name])
    forecast_payload = fetch_forecast(location['latitude'], location['longitude'])
    current = forecast_payload.get('current') or {}
    daily = forecast_payload.get('daily') or {}
    hourly = forecast_payload.get('hourly') or {}
    analysis = analyse_weather(current=current, daily=daily, hourly=hourly)
    observed_at = parse_observed_at(current.get('time')) or timezone.now()
    if timezone.is_naive(observed_at):
        observed_at = timezone.make_aware(observed_at, timezone.get_current_timezone())

    resolved_parts = [
        location.get('name'),
        location.get('admin1'),
        location.get('country'),
    ]
    resolved_location = ', '.join(part for part in resolved_parts if part)

    report = WeatherReport.objects.create(
        pond=pond,
        location_query=pond.location,
        resolved_location=resolved_location or pond.location,
        country=location.get('country') or '',
        latitude=Decimal(str(location['latitude'])),
        longitude=Decimal(str(location['longitude'])),
        timezone=forecast_payload.get('timezone') or location.get('timezone') or '',
        observed_at=observed_at,
        forecast_date=observed_at.date(),
        air_temperature=round(float(current.get('temperature_2m') or 0), 1),
        rainfall_probability=analysis['rainfall_probability'],
        rainfall_mm=round(float(current.get('precipitation') or 0), 1),
        wind_speed=round(float(current.get('wind_speed_10m') or 0), 1),
        humidity=round(float(current.get('relative_humidity_2m') or 0), 1),
        uv_index=analysis['uv_index'],
        cloud_cover=round(float(current.get('cloud_cover') or 0), 1),
        atmospheric_pressure=round(float(current.get('pressure_msl') or 0), 1),
        weather_code=current.get('weather_code'),
        fish_weather_risk=analysis['fish_weather_risk'],
        disease_risk=analysis['disease_risk'],
        pond_impact=analysis['pond_impact'],
        feeding_recommendation=analysis['feeding_recommendation'],
        do_prediction=analysis['do_prediction'],
        rain_impact=analysis['rain_impact'],
        alerts=analysis['alerts'],
        forecast=analysis['forecast'],
        raw_payload=forecast_payload,
        source=SOURCE_NAME,
        source_url=SOURCE_URL,
    )
    create_weather_notifications(report)
    return report
