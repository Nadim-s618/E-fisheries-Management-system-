import json
import ssl
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
from django.conf import settings


GEOCODING_URL = 'https://api.openweathermap.org/geo/1.0/direct'
CURRENT_WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
SOURCE_NAME = 'OpenWeather'
SOURCE_URL = 'https://openweathermap.org/api'
USER_AGENT = 'E-Fisheries-Management-System/1.0'


class WeatherServiceError(Exception):
    pass


def get_api_key():
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', '').strip()
    if not api_key:
        raise WeatherServiceError(
            'OpenWeather API key is missing. Add OPENWEATHER_API_KEY to backend/.env.',
        )
    return api_key


def fetch_json(url, params):
    timeout = getattr(settings, 'OPENWEATHER_TIMEOUT_SECONDS', 8)
    request_params = {**params, 'appid': get_api_key()}
    request_url = f'{url}?{urlencode(request_params)}'
    request = Request(request_url, headers={'User-Agent': USER_AGENT})

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        with urlopen(request, context=ssl_context, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        detail = read_http_error_detail(exc)
        message = f'OpenWeather returned HTTP {exc.code}'
        if detail:
            message = f'{message}: {detail}'
        raise WeatherServiceError(f'{message}.') from exc
    except URLError as exc:
        raise WeatherServiceError(f'Could not reach OpenWeather: {exc.reason}.') from exc
    except Exception as exc:
        raise WeatherServiceError(f'Could not reach OpenWeather: {exc}.') from exc


def read_http_error_detail(exc):
    try:
        payload = json.loads(exc.read().decode('utf-8'))
    except Exception:
        return ''
    return payload.get('message') or payload.get('cod') or ''


def geocode_location(location, fallback_terms=None):
    candidates = build_location_candidates(location, fallback_terms or [])
    if not candidates:
        raise WeatherServiceError('Pond location is too short for weather lookup.')

    for candidate in candidates:
        result = search_location(candidate)
        if result:
            return result

    tried_terms = ', '.join(candidates)
    raise WeatherServiceError(f'No weather location found. Tried: {tried_terms}.')


def search_location(location):
    params = {
        'q': format_location_query(location),
        'limit': 1,
    }

    data = fetch_json(GEOCODING_URL, params)
    if not data:
        return None

    result = data[0]
    return {
        'name': result.get('name') or location,
        'admin1': result.get('state') or '',
        'country': result.get('country') or '',
        'latitude': result.get('lat'),
        'longitude': result.get('lon'),
        'timezone': '',
    }


def format_location_query(location):
    country_code = getattr(settings, 'OPENWEATHER_GEOCODING_COUNTRY_CODE', '').strip()
    if country_code and ',' not in location:
        return f'{location},{country_code}'
    return location


def build_location_candidates(location, fallback_terms):
    raw_terms = [location, *fallback_terms]
    candidates = []

    for raw_term in raw_terms:
        term = (raw_term or '').strip()
        if len(term) < 2:
            continue
        add_candidate(candidates, term)

        normalized = term.lower()
        if 'cumilla' in normalized:
            add_candidate(candidates, replace_case_insensitive(term, 'cumilla', 'comilla'))

    return candidates


def add_candidate(candidates, term):
    cleaned = ' '.join(term.split())
    if cleaned and cleaned.lower() not in {item.lower() for item in candidates}:
        candidates.append(cleaned)


def replace_case_insensitive(value, old, new):
    index = value.lower().find(old.lower())
    if index == -1:
        return value
    return f'{value[:index]}{new}{value[index + len(old):]}'


def fetch_forecast(latitude, longitude):
    current_payload = fetch_json(CURRENT_WEATHER_URL, weather_params(latitude, longitude))
    forecast_payload = fetch_json(FORECAST_URL, weather_params(latitude, longitude))
    return normalize_weather_payload(current_payload, forecast_payload)


def weather_params(latitude, longitude):
    return {
        'lat': latitude,
        'lon': longitude,
        'units': 'metric',
    }


def normalize_weather_payload(current_payload, forecast_payload):
    timezone_offset = current_payload.get('timezone')
    if timezone_offset is None:
        timezone_offset = (forecast_payload.get('city') or {}).get('timezone')

    return {
        'source_payload': {
            'current': current_payload,
            'forecast': forecast_payload,
        },
        'timezone': format_timezone(timezone_offset),
        'current': normalize_current(current_payload),
        'daily': normalize_daily(forecast_payload),
        'hourly': normalize_forecast_rows(forecast_payload),
    }


def normalize_current(payload):
    main = payload.get('main') or {}
    wind = payload.get('wind') or {}
    clouds = payload.get('clouds') or {}
    weather = first_item(payload.get('weather'))

    return {
        'time': unix_to_iso(payload.get('dt')),
        'temperature_2m': main.get('temp'),
        'relative_humidity_2m': main.get('humidity'),
        'precipitation': precipitation_1h(payload),
        'rain': (payload.get('rain') or {}).get('1h', 0),
        'weather_code': normalize_weather_code((weather or {}).get('id')),
        'cloud_cover': clouds.get('all'),
        'pressure_msl': main.get('sea_level') or main.get('pressure'),
        'surface_pressure': main.get('grnd_level') or main.get('pressure'),
        'wind_speed_10m': meters_per_second_to_kmh(wind.get('speed')),
        'wind_gusts_10m': meters_per_second_to_kmh(wind.get('gust')),
    }


def normalize_forecast_rows(payload):
    rows = payload.get('list') or []
    hourly = {
        'time': [],
        'temperature_2m': [],
        'relative_humidity_2m': [],
        'precipitation_probability': [],
        'precipitation': [],
        'rain': [],
        'weather_code': [],
        'cloud_cover': [],
        'pressure_msl': [],
        'wind_speed_10m': [],
        'wind_gusts_10m': [],
        'interval_hours': 3,
    }

    for row in rows:
        main = row.get('main') or {}
        wind = row.get('wind') or {}
        clouds = row.get('clouds') or {}
        weather = first_item(row.get('weather'))

        hourly['time'].append(unix_to_iso(row.get('dt')))
        hourly['temperature_2m'].append(main.get('temp'))
        hourly['relative_humidity_2m'].append(main.get('humidity'))
        hourly['precipitation_probability'].append(round(float(row.get('pop') or 0) * 100, 1))
        hourly['precipitation'].append(precipitation_3h(row))
        hourly['rain'].append((row.get('rain') or {}).get('3h', 0))
        hourly['weather_code'].append(normalize_weather_code((weather or {}).get('id')))
        hourly['cloud_cover'].append(clouds.get('all'))
        hourly['pressure_msl'].append(main.get('sea_level') or main.get('pressure'))
        hourly['wind_speed_10m'].append(meters_per_second_to_kmh(wind.get('speed')))
        hourly['wind_gusts_10m'].append(meters_per_second_to_kmh(wind.get('gust')))

    return hourly


def normalize_daily(payload):
    rows = payload.get('list') or []
    return {
        'weather_code': [normalize_weather_code((first_item(row.get('weather')) or {}).get('id')) for row in rows[:1]],
        'precipitation_probability_max': [
            round(max([float(row.get('pop') or 0) for row in rows[:8]] or [0]) * 100, 1),
        ],
    }


def first_item(value):
    return value[0] if value else None


def precipitation_1h(payload):
    return safe_number((payload.get('rain') or {}).get('1h')) + safe_number((payload.get('snow') or {}).get('1h'))


def precipitation_3h(payload):
    return safe_number((payload.get('rain') or {}).get('3h')) + safe_number((payload.get('snow') or {}).get('3h'))


def safe_number(value, default=0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def meters_per_second_to_kmh(value):
    if value is None:
        return None
    return round(safe_number(value) * 3.6, 1)


def normalize_weather_code(code):
    if code is None:
        return None
    if code == 800:
        return 0
    if code == 801:
        return 2
    if 802 <= code <= 804:
        return 3
    if 200 <= code < 300:
        return 95
    if 300 <= code < 400:
        return 53
    if 500 <= code < 600:
        return 63 if code in {502, 503, 504, 522, 531} else 61
    if 600 <= code < 700:
        return 71
    if 700 <= code < 800:
        return 45
    return code


def unix_to_iso(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def format_timezone(offset_seconds):
    if offset_seconds is None:
        return ''
    sign = '+' if offset_seconds >= 0 else '-'
    absolute = abs(int(offset_seconds))
    hours = absolute // 3600
    minutes = (absolute % 3600) // 60
    return f'UTC{sign}{hours:02d}:{minutes:02d}'