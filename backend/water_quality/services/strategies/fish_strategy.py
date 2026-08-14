from copy import deepcopy

from water_quality.utils.thresholds import WATER_QUALITY_THRESHOLDS

from .base import WaterQualityStrategy


class FishWaterQualityStrategy(WaterQualityStrategy):
    name = 'fish'

    def __init__(self):
        thresholds = deepcopy(WATER_QUALITY_THRESHOLDS)
        thresholds['temperature'] = {
            'normal_range': '24-32 °C',
            'good': (24.0, 32.0),
            'warning': (20.0, 34.0),
        }
        thresholds['ph'] = {
            'normal_range': '6.5-8.5',
            'good': (6.5, 8.5),
            'warning': (6.0, 9.0),
        }
        super().__init__(thresholds)
