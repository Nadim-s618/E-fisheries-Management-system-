from copy import deepcopy

from water_quality.utils.thresholds import WATER_QUALITY_THRESHOLDS

from .base import WaterQualityStrategy


class ShrimpWaterQualityStrategy(WaterQualityStrategy):
    name = 'shrimp'

    def __init__(self):
        thresholds = deepcopy(WATER_QUALITY_THRESHOLDS)
        thresholds.update({
            'temperature': {
                'normal_range': '24-30 °C',
                'good': (24.0, 30.0),
                'warning': (21.0, 33.0),
            },
            'ph': {
                'normal_range': '7.0-8.5',
                'good': (7.0, 8.5),
                'warning': (6.5, 9.0),
            },
            'dissolved_oxygen': {
                'normal_range': '5-8 mg/L',
                'good': (5.0, 8.0),
                'warning': (4.0, 10.0),
            },
            'ammonia': {
                'normal_range': '0-0.02 mg/L',
                'good': (0.0, 0.02),
                'warning': (0.0, 0.05),
            },
            'nitrite': {
                'normal_range': '0-0.1 mg/L',
                'good': (0.0, 0.1),
                'warning': (0.0, 0.3),
            },
            'salinity': {
                'normal_range': '5-25 ppt',
                'good': (5.0, 25.0),
                'warning': (2.0, 30.0),
            },
        })
        super().__init__(thresholds)
