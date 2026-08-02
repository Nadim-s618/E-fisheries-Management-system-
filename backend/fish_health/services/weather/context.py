from weather.models import WeatherReport


def get_latest_weather_snapshot(pond):
    report = (
        WeatherReport.objects
        .filter(pond=pond)
        .order_by('-observed_at', '-created_at')
        .first()
    )

    if report is None:
        return {}

    return {
        'id': report.id,
        'observed_at': report.observed_at.isoformat(),
        'forecast_date': report.forecast_date.isoformat(),
        'air_temperature': report.air_temperature,
        'rainfall_probability': report.rainfall_probability,
        'rainfall_mm': report.rainfall_mm,
        'wind_speed': report.wind_speed,
        'humidity': report.humidity,
        'fish_weather_risk': report.fish_weather_risk,
        'disease_risk': report.disease_risk,
        'alerts': report.alerts,
    }


def get_weather_risk_notes(snapshot):
    if not snapshot:
        return []

    notes = []

    if snapshot.get('disease_risk') in {'Moderate', 'High'}:
        notes.append(f"Latest weather disease risk is {snapshot['disease_risk']}.")
    if snapshot.get('rainfall_probability') is not None and snapshot['rainfall_probability'] >= 70:
        notes.append('Rain risk is high; watch overflow, runoff, and sudden temperature shifts.')
    if snapshot.get('air_temperature') is not None and snapshot['air_temperature'] >= 34:
        notes.append('High air temperature can reduce oxygen margin in ponds.')

    return notes
