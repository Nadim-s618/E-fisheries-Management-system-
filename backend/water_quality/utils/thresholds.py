STATUS_GOOD = 'Good'
STATUS_WARNING = 'Warning'
STATUS_DANGER = 'Danger'


WATER_QUALITY_THRESHOLDS = {
    'temperature': {
        'normal_range': '24-30 °C',
        'good': (24.0, 30.0),
        'warning': (20.0, 34.0),
    },
    'ph': {
        'normal_range': '6.5-8.5',
        'good': (6.5, 8.5),
        'warning': (6.0, 9.0),
    },
    'dissolved_oxygen': {
        'normal_range': '5-8 mg/L',
        'good': (5.0, 8.0),
        'warning': (3.0, 10.0),
    },
    'ammonia': {
        'normal_range': '0-0.02 mg/L',
        'good': (0.0, 0.02),
        'warning': (0.0, 0.05),
    },
    'nitrite': {
        'normal_range': '0-0.2 mg/L',
        'good': (0.0, 0.2),
        'warning': (0.0, 0.5),
    },
    'nitrate': {
        'normal_range': '0-40 mg/L',
        'good': (0.0, 40.0),
        'warning': (0.0, 80.0),
    },
    'turbidity': {
        'normal_range': '20-80 NTU',
        'good': (20.0, 80.0),
        'warning': (10.0, 120.0),
    },
    'salinity': {
        'normal_range': '0-25 ppt',
        'good': (0.0, 25.0),
        'warning': (0.0, 35.0),
    },
    'water_level': {
        'normal_range': '3-6 ft',
        'good': (3.0, 6.0),
        'warning': (2.0, 8.0),
    },
}
