from copy import deepcopy

from water_quality.utils.thresholds import (
    STATUS_DANGER,
    STATUS_GOOD,
    STATUS_WARNING,
    WATER_QUALITY_THRESHOLDS,
)


class WaterQualityStrategy:
    name = 'general'

    def __init__(self, thresholds=None):
        self.thresholds = thresholds or deepcopy(WATER_QUALITY_THRESHOLDS)

    def analyse(self, values):
        parameters = [
            self.analyse_parameter(parameter, values[parameter])
            for parameter in values
            if values[parameter] is not None
        ]
        return {
            'strategy': self.name,
            'overall_status': self.calculate_overall_status(parameters),
            'parameters': parameters,
        }

    def analyse_parameter(self, parameter, value):
        threshold = self.thresholds[parameter]
        return {
            'parameter': parameter,
            'value': value,
            'normal_range': threshold['normal_range'],
            'status': self.calculate_parameter_status(value, threshold),
        }

    @staticmethod
    def calculate_parameter_status(value, threshold):
        good_min, good_max = threshold['good']
        warning_min, warning_max = threshold['warning']

        if good_min <= value <= good_max:
            return STATUS_GOOD
        if warning_min <= value <= warning_max:
            return STATUS_WARNING
        return STATUS_DANGER

    @staticmethod
    def calculate_overall_status(parameters):
        statuses = {parameter['status'] for parameter in parameters}
        if STATUS_DANGER in statuses:
            return STATUS_DANGER
        if STATUS_WARNING in statuses:
            return STATUS_WARNING
        return STATUS_GOOD


def get_strategy_for_species(species=None):
    normalized = str(species or '').strip().lower()

    if 'shrimp' in normalized or 'prawn' in normalized:
        from .shrimp_strategy import ShrimpWaterQualityStrategy

        return ShrimpWaterQualityStrategy()

    if normalized:
        from .fish_strategy import FishWaterQualityStrategy

        return FishWaterQualityStrategy()

    from .general_strategy import GeneralWaterQualityStrategy

    return GeneralWaterQualityStrategy()
