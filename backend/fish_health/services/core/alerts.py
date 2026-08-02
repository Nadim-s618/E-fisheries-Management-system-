from core.models import Notification
from fish_health.models import HealthRecord


PRIORITY_BY_SEVERITY = {
    HealthRecord.Severity.CRITICAL: Notification.Priority.HIGH,
    HealthRecord.Severity.HIGH: Notification.Priority.HIGH,
    HealthRecord.Severity.MODERATE: Notification.Priority.MEDIUM,
}


def create_health_notifications(record):
    priority = PRIORITY_BY_SEVERITY.get(record.severity)
    if priority is None:
        return []

    top_disease = record.possible_diseases[0]['name'] if record.possible_diseases else 'Unknown disease'
    parameter = 'Fish health'
    reason = (
        f'{record.pond.name} has a {record.severity.lower()} health record. '
        f'Possible disease: {top_disease}. {record.ai_recommendation[:220]}'
    )

    if Notification.objects.filter(
        user=record.created_by,
        pond=record.pond,
        parameter=parameter,
        reason=reason,
        is_read=False,
    ).exists():
        return []

    return [Notification.objects.create(
        user=record.created_by,
        pond=record.pond,
        parameter=parameter,
        current_value=record.severity,
        reason=reason,
        priority=priority,
    )]
