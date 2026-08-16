from decimal import Decimal

from .fish_strategy import FishFeedingStrategy


class PangasiusFeedingStrategy(FishFeedingStrategy):
    name = 'pangasius'

    def get_feeding_rate(self, average_weight_g):
        if average_weight_g < 50:
            return Decimal('0.045')
        if average_weight_g < 150:
            return Decimal('0.035')
        if average_weight_g < 500:
            return Decimal('0.028')
        return Decimal('0.020')
