from core.models import Notification


def create_feeding_notification(pond, parameter, current_value, reason, priority=Notification.Priority.LOW):
    if Notification.objects.filter(
        user=pond.owner,
        pond=pond,
        parameter=parameter,
        current_value=current_value,
        reason=reason,
        is_read=False,
    ).exists():
        return None

    return Notification.objects.create(
        user=pond.owner,
        pond=pond,
        parameter=parameter,
        current_value=current_value,
        reason=reason,
        priority=priority,
    )
