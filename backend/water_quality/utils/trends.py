TREND_INCREASING = '↑'
TREND_DECREASING = '↓'
TREND_STABLE = '→'


TREND_PARAMETERS = (
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


def calculate_trends(latest_reading, previous_reading):
    return {
        parameter: calculate_trend(
            get_reading_value(latest_reading, parameter),
            get_reading_value(previous_reading, parameter),
        )
        for parameter in TREND_PARAMETERS
    }


def calculate_trend(latest_value, previous_value):
    if latest_value is None or previous_value is None:
        return TREND_STABLE

    if latest_value > previous_value:
        return TREND_INCREASING

    if latest_value < previous_value:
        return TREND_DECREASING

    return TREND_STABLE


def get_reading_value(reading, parameter):
    if reading is None:
        return None

    if isinstance(reading, dict):
        return reading.get(parameter)

    return getattr(reading, parameter, None)
