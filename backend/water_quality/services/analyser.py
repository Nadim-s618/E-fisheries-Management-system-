from water_quality.utils.thresholds import (
    STATUS_DANGER,
    STATUS_GOOD,
    STATUS_WARNING,
    WATER_QUALITY_THRESHOLDS,
)


PARAMETER_ORDER = (
    'temperature',
    'ph',
    'dissolved_oxygen',
    'ammonia',
    'nitrite',
    'nitrate',
    'turbidity',
    'salinity',
    'water_level',
)


def analyse_water_quality(
    *,
    temperature,
    ph,
    dissolved_oxygen,
    ammonia,
    nitrite,
    nitrate,
    turbidity,
    salinity=None,
    water_level,
):
    values = {
        'temperature': temperature,
        'ph': ph,
        'dissolved_oxygen': dissolved_oxygen,
        'ammonia': ammonia,
        'nitrite': nitrite,
        'nitrate': nitrate,
        'turbidity': turbidity,
        'salinity': salinity,
        'water_level': water_level,
    }
    parameters = [
        analyse_parameter(parameter, values[parameter])
        for parameter in PARAMETER_ORDER
        if values[parameter] is not None
    ]

    return {
        'overall_status': calculate_overall_status(parameters),
        'parameters': parameters,
    }


def analyse_parameter(parameter, value):
    threshold = WATER_QUALITY_THRESHOLDS[parameter]

    return {
        'parameter': parameter,
        'value': value,
        'normal_range': threshold['normal_range'],
        'status': calculate_parameter_status(value, threshold),
    }


def calculate_parameter_status(value, threshold):
    good_min, good_max = threshold['good']
    warning_min, warning_max = threshold['warning']

    if good_min <= value <= good_max:
        return STATUS_GOOD

    if warning_min <= value <= warning_max:
        return STATUS_WARNING

    return STATUS_DANGER


def calculate_overall_status(parameters):
    statuses = [parameter['status'] for parameter in parameters]

    if STATUS_DANGER in statuses:
        return STATUS_DANGER

    if STATUS_WARNING in statuses:
        return STATUS_WARNING

    return STATUS_GOOD
