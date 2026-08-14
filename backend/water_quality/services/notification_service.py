from core.models import Notification
from water_quality.services.analyser import analyse_water_quality, get_primary_species
from water_quality.utils.thresholds import STATUS_DANGER, STATUS_WARNING


PRIORITY_HIGH = 'High'
PRIORITY_MEDIUM = 'Medium'


def create_water_quality_notifications(reading):
    analysis = analyse_water_quality(
        temperature=reading.temperature,
        ph=reading.ph,
        dissolved_oxygen=reading.dissolved_oxygen,
        ammonia=reading.ammonia,
        nitrite=reading.nitrite,
        nitrate=reading.nitrate,
        turbidity=reading.turbidity,
        salinity=reading.salinity,
        water_level=reading.water_level,
        species=get_primary_species(reading.pond),
    )
    notifications = []

    for parameter in analysis['parameters']:
        priority = get_priority(parameter['status'])

        if priority is None:
            continue

        notifications.append(Notification.objects.create(
            user=reading.pond.owner,
            pond=reading.pond,
            parameter=parameter['parameter'],
            current_value=str(parameter['value']),
            reason=build_reason(parameter),
            priority=priority,
        ))

    return notifications


def get_priority(status):
    if status == STATUS_DANGER:
        return PRIORITY_HIGH

    if status == STATUS_WARNING:
        return PRIORITY_MEDIUM

    return None


def build_reason(parameter):
    return (
        f"{parameter['parameter']} is {parameter['status']}. "
        f"Current value is {parameter['value']}; normal range is {parameter['normal_range']}."
    )
