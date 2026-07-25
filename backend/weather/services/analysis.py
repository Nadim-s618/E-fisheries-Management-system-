from datetime import datetime
from math import ceil


def safe_number(value, default=0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def analyse_weather(current, daily, hourly):
    temperature = safe_number(current.get('temperature_2m'))
    humidity = safe_number(current.get('relative_humidity_2m'))
    rain_mm = safe_number(current.get('precipitation'))
    wind_speed = safe_number(current.get('wind_speed_10m'))
    cloud_cover = safe_number(current.get('cloud_cover'))
    pressure = safe_number(current.get('pressure_msl'), 1010)
    uv_index = safe_number(first_value(daily, 'uv_index_max'), None)
    rain_probability = safe_number(
        nearest_hour_value(hourly, 'precipitation_probability', current.get('time')),
        safe_number(first_value(daily, 'precipitation_probability_max')),
    )
    next_24h = next_hourly_rows(hourly, current.get('time'), hours=24)
    next_48h = next_hourly_rows(hourly, current.get('time'), hours=48)
    next_rain_mm = sum(safe_number(row.get('precipitation')) for row in next_24h)
    next_max_rain_probability = max(
        [safe_number(row.get('precipitation_probability')) for row in next_24h] or [rain_probability],
    )
    next_max_wind = max(
        [safe_number(row.get('wind_speed_10m')) for row in next_24h] or [wind_speed],
    )
    morning_do, night_do = predict_dissolved_oxygen(
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        cloud_cover=cloud_cover,
        rain_probability=rain_probability,
        rain_mm=next_rain_mm,
        pressure=pressure,
    )
    alerts = build_alerts(
        next_48h=next_48h,
        temperature=temperature,
        wind_speed=next_max_wind,
        rain_probability=next_max_rain_probability,
        rain_mm=next_rain_mm,
        night_do=night_do,
    )
    fish_risk = classify_fish_weather_risk(
        temperature=temperature,
        humidity=humidity,
        wind_speed=next_max_wind,
        rain_probability=next_max_rain_probability,
        rain_mm=next_rain_mm,
        pressure=pressure,
        uv_index=uv_index,
        night_do=night_do,
    )
    disease_risk = classify_disease_risk(
        temperature=temperature,
        humidity=humidity,
        cloud_cover=cloud_cover,
        rain_probability=next_max_rain_probability,
        rain_mm=next_rain_mm,
    )

    return {
        'rainfall_probability': round(rain_probability, 1),
        'uv_index': None if uv_index is None else round(uv_index, 1),
        'fish_weather_risk': fish_risk,
        'disease_risk': disease_risk,
        'pond_impact': build_pond_impact(
            temperature=temperature,
            humidity=humidity,
            cloud_cover=cloud_cover,
            wind_speed=wind_speed,
            rain_probability=rain_probability,
            rain_mm=next_rain_mm,
            pressure=pressure,
            night_do=night_do,
        ),
        'feeding_recommendation': build_feeding_recommendations(
            temperature=temperature,
            rain_probability=next_max_rain_probability,
            rain_mm=next_rain_mm,
            wind_speed=next_max_wind,
            night_do=night_do,
        ),
        'do_prediction': {
            'morning': round(morning_do, 1),
            'night': round(night_do, 1),
            'unit': 'mg/L',
            'action': 'Turn on aerator' if night_do < 5.5 else 'Routine aeration',
        },
        'rain_impact': build_rain_impact(next_max_rain_probability, next_rain_mm),
        'alerts': alerts,
        'forecast': build_forecast(next_48h),
    }


def first_value(payload, key):
    values = payload.get(key) or []
    return values[0] if values else None


def nearest_hour_value(hourly, key, current_time):
    times = hourly.get('time') or []
    values = hourly.get(key) or []
    if not times or not values:
        return None

    if current_time in times:
        index = times.index(current_time)
        return values[index] if index < len(values) else None

    return values[0]


def next_hourly_rows(hourly, current_time, hours=24):
    times = hourly.get('time') or []
    if not times:
        return []

    interval_hours = max(safe_number(hourly.get('interval_hours'), 1), 1)
    max_rows = int(ceil(hours / interval_hours))
    start = 0
    if current_time in times:
        start = times.index(current_time)
    rows = []
    keys = [
        key for key, value in hourly.items()
        if key not in {'time', 'interval_hours'} and isinstance(value, list)
    ]

    for offset, time_value in enumerate(times[start:start + max_rows]):
        row = {'time': time_value, '_interval_hours': interval_hours}
        for key in keys:
            values = hourly.get(key) or []
            value_index = start + offset
            row[key] = values[value_index] if value_index < len(values) else None
        rows.append(row)

    return rows


def predict_dissolved_oxygen(
    temperature,
    humidity,
    wind_speed,
    cloud_cover,
    rain_probability,
    rain_mm,
    pressure,
):
    morning = 8.0
    morning -= max(0, temperature - 28) * 0.18
    morning += min(wind_speed, 18) * 0.025
    morning -= max(0, humidity - 80) * 0.012
    morning -= max(0, cloud_cover - 70) * 0.006
    morning -= max(0, 1005 - pressure) * 0.015
    morning -= min(rain_mm, 30) * 0.015

    night = morning - 1.25
    night -= max(0, temperature - 30) * 0.1
    night -= max(0, rain_probability - 60) * 0.01

    return clamp(morning, 2.5, 10.5), clamp(night, 2.0, 9.5)


def classify_fish_weather_risk(
    temperature,
    humidity,
    wind_speed,
    rain_probability,
    rain_mm,
    pressure,
    uv_index,
    night_do,
):
    danger_flags = [
        temperature >= 36,
        rain_mm >= 35,
        wind_speed >= 36,
        pressure <= 995,
        night_do < 4.5,
    ]
    warning_flags = [
        temperature >= 32 or temperature <= 20,
        humidity >= 85,
        rain_probability >= 60,
        rain_mm >= 12,
        wind_speed >= 20,
        uv_index is not None and uv_index >= 8,
        night_do < 5.5,
    ]

    if any(danger_flags):
        return 'High'
    if sum(1 for flag in warning_flags if flag) >= 2:
        return 'Moderate'
    return 'Low'


def classify_disease_risk(temperature, humidity, cloud_cover, rain_probability, rain_mm):
    if rain_mm >= 35 or (humidity >= 92 and cloud_cover >= 80 and 24 <= temperature <= 33):
        return 'High'
    if rain_probability >= 60 or (humidity >= 80 and cloud_cover >= 60 and 22 <= temperature <= 34):
        return 'Moderate'
    return 'Low'


def build_pond_impact(
    temperature,
    humidity,
    cloud_cover,
    wind_speed,
    rain_probability,
    rain_mm,
    pressure,
    night_do,
):
    impacts = []
    if temperature >= 32:
        impacts.append('Warm air can raise pond temperature and reduce oxygen holding capacity.')
    if humidity >= 85 and cloud_cover >= 70:
        impacts.append('Humid cloudy weather may slow oxygen recovery before dawn.')
    if rain_probability >= 60 or rain_mm >= 12:
        impacts.append('Rain can dilute minerals, lower pH and increase turbidity.')
    if wind_speed >= 20:
        impacts.append('Strong wind may mix pond layers and stress feeding behavior.')
    if pressure <= 1000:
        impacts.append('Low pressure often comes with unstable weather and lower oxygen comfort.')
    if night_do < 5.5:
        impacts.append('Predicted night DO is low enough to require aerator readiness.')
    if not impacts:
        impacts.append('Current weather has low immediate impact on routine pond operation.')
    return {
        'summary': impacts[0],
        'items': impacts,
    }


def build_feeding_recommendations(temperature, rain_probability, rain_mm, wind_speed, night_do):
    recommendations = []

    if 24 <= temperature <= 31 and rain_probability < 60 and night_do >= 5.5:
        recommendations.append({'status': 'ok', 'text': 'Feed at 6 AM'})
    else:
        recommendations.append({'status': 'caution', 'text': 'Use a smaller early morning feed after checking fish activity'})

    if temperature >= 32 or rain_probability >= 60 or rain_mm >= 12:
        recommendations.append({'status': 'warning', 'text': 'Reduce afternoon feeding'})
    else:
        recommendations.append({'status': 'ok', 'text': 'Normal afternoon feeding can continue'})

    if wind_speed >= 24:
        recommendations.append({'status': 'warning', 'text': 'Avoid surface feeding during strong wind'})

    if night_do < 5.5:
        recommendations.append({'status': 'warning', 'text': 'Run aerator before night feeding decisions'})

    return recommendations


def build_rain_impact(rain_probability, rain_mm):
    ph = 'Stable'
    turbidity = 'Stable'
    overflow = 'Low'

    if rain_probability >= 60 or rain_mm >= 10:
        ph = 'Likely down'
        turbidity = 'Likely up'
        overflow = 'Watch'
    if rain_mm >= 30:
        ph = 'Sharp drop possible'
        turbidity = 'High'
        overflow = 'High'

    return {
        'ph': ph,
        'turbidity': turbidity,
        'overflow': overflow,
        'next_24h_rain_mm': round(rain_mm, 1),
    }


def build_alerts(next_48h, temperature, wind_speed, rain_probability, rain_mm, night_do):
    alerts = []
    heavy_rain = find_heavy_rain(next_48h)

    if heavy_rain:
        alerts.append({
            'level': 'warning',
            'text': f'Heavy rain in {heavy_rain["hours"]} hours',
        })
    elif rain_probability >= 70:
        alerts.append({'level': 'warning', 'text': 'High rain chance in the next 24 hours'})

    if rain_mm >= 30:
        alerts.append({'level': 'danger', 'text': 'Overflow risk'})
    elif rain_mm >= 15:
        alerts.append({'level': 'warning', 'text': 'Check pond water level after rainfall'})

    if night_do < 5.5:
        alerts.append({'level': 'warning', 'text': 'Check aerator tonight'})

    if wind_speed >= 32:
        alerts.append({'level': 'warning', 'text': 'Strong wind may disturb pond surface feeding'})

    if temperature >= 35:
        alerts.append({'level': 'danger', 'text': 'Heat stress risk for fish'})

    if not alerts:
        alerts.append({'level': 'ok', 'text': 'No bad weather warning for the next 24 hours'})

    return alerts


def find_heavy_rain(rows):
    for index, row in enumerate(rows):
        probability = safe_number(row.get('precipitation_probability'))
        precipitation = safe_number(row.get('precipitation'))
        if probability >= 70 and precipitation >= 3:
            interval_hours = max(safe_number(row.get('_interval_hours'), 1), 1)
            return {'hours': int(index * interval_hours), 'time': row.get('time')}
    return None


def build_forecast(rows):
    if not rows:
        return []

    interval_hours = max(safe_number(rows[0].get('_interval_hours'), 1), 1)
    max_rows = int(ceil(24 / interval_hours))
    step = max(int(round(6 / interval_hours)), 1)
    checkpoints = []
    for row in rows[:max_rows:step]:
        checkpoints.append({
            'time': row.get('time'),
            'air_temperature': round(safe_number(row.get('temperature_2m')), 1),
            'rainfall_probability': round(safe_number(row.get('precipitation_probability')), 1),
            'rainfall_mm': round(safe_number(row.get('precipitation')), 1),
            'wind_speed': round(safe_number(row.get('wind_speed_10m')), 1),
            'cloud_cover': round(safe_number(row.get('cloud_cover')), 1),
        })
    return checkpoints


def parse_observed_at(value):
    if not value:
        return None
    return datetime.fromisoformat(value)
