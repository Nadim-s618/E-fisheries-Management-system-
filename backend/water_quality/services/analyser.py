from .strategies import get_strategy_for_species


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


def get_primary_species(pond):
    """Return the first active species used in a pond, if one exists."""
    from stocks.models import FishStock

    stock = (
        FishStock.objects
        .filter(
            pond=pond,
            status=FishStock.Status.ACTIVE,
            current_quantity__gt=0,
        )
        .order_by('id')
        .first()
    )
    return stock.species if stock else None


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
    species=None,
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
    ordered_values = {
        parameter: values[parameter]
        for parameter in PARAMETER_ORDER
        if values[parameter] is not None
    }
    return get_strategy_for_species(species).analyse(ordered_values)


def analyse_parameter(parameter, value):
    return get_strategy_for_species().analyse_parameter(parameter, value)


def calculate_parameter_status(value, threshold):
    return get_strategy_for_species().calculate_parameter_status(value, threshold)


def calculate_overall_status(parameters):
    return get_strategy_for_species().calculate_overall_status(parameters)
