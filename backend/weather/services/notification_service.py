from core.models import Notification


PRIORITY_BY_ALERT_LEVEL = {
    'danger': Notification.Priority.HIGH,
    'warning': Notification.Priority.MEDIUM,
}


def create_weather_notifications(report):
    notifications = []

    for alert in report.alerts or []:
        level = str(alert.get('level') or '').lower()
        priority = PRIORITY_BY_ALERT_LEVEL.get(level)

        if priority is None:
            continue

        parameter = build_parameter(alert)
        current_value = build_current_value(report, alert)
        reason = build_reason(report, alert)

        if has_duplicate_unread_notification(report, parameter, reason):
            continue

        notifications.append(Notification.objects.create(
            user=report.pond.owner,
            pond=report.pond,
            parameter=parameter,
            current_value=current_value,
            reason=reason,
            priority=priority,
        ))

    return notifications


def has_duplicate_unread_notification(report, parameter, reason):
    return Notification.objects.filter(
        user=report.pond.owner,
        pond=report.pond,
        parameter=parameter,
        reason=reason,
        is_read=False,
    ).exists()


def build_parameter(alert):
    text = str(alert.get('text') or '').lower()

    if 'rain' in text or 'overflow' in text or 'water level' in text:
        return 'Weather rainfall'
    if 'heat' in text or 'temperature' in text:
        return 'Air temperature'
    if 'wind' in text:
        return 'Wind speed'
    if 'aerator' in text or 'oxygen' in text:
        return 'Predicted oxygen'

    return 'Weather alert'


def build_current_value(report, alert):
    parameter = build_parameter(alert)

    if parameter == 'Weather rainfall':
        next_rain = (report.rain_impact or {}).get('next_24h_rain_mm')
        return f'{next_rain} mm next 24h, {report.rainfall_probability}% chance'
    if parameter == 'Air temperature':
        return f'{report.air_temperature} °C'
    if parameter == 'Wind speed':
        return f'{report.wind_speed} km/h'
    if parameter == 'Predicted oxygen':
        night_do = (report.do_prediction or {}).get('night')
        unit = (report.do_prediction or {}).get('unit', 'mg/L')
        return f'{night_do} {unit} tonight'

    return report.fish_weather_risk


def build_reason(report, alert):
    text = alert.get('text') or 'Weather conditions need attention.'
    return f'{text}. Check {report.pond.name} before feeding or changing pond operation.'
