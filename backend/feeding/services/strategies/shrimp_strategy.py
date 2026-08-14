from decimal import Decimal

from .base import FeedingStrategy


class ShrimpFeedingStrategy(FeedingStrategy):
    name = 'shrimp'

    def get_feeding_rate(self, average_weight_g):
        if average_weight_g < 5:
            return Decimal('0.080')
        if average_weight_g < 20:
            return Decimal('0.060')
        if average_weight_g < 50:
            return Decimal('0.040')
        return Decimal('0.025')

    def get_meal_times(self, multiplier):
        if multiplier < Decimal('0.70'):
            return ['09:00']
        return ['07:00', '12:30', '18:30']
