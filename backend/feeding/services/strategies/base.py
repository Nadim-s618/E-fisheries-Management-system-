from decimal import Decimal


class FeedingStrategy:
    name = 'general'

    def get_feeding_rate(self, average_weight_g):
        if average_weight_g < 50:
            return Decimal('0.040')
        if average_weight_g < 150:
            return Decimal('0.030')
        if average_weight_g < 500:
            return Decimal('0.025')
        return Decimal('0.018')

    def get_meal_times(self, multiplier):
        return ['09:00'] if multiplier < Decimal('0.70') else ['08:00', '16:30']


def get_feeding_strategy_for_species(species=None):
    normalized = str(species or '').strip().lower()

    if 'shrimp' in normalized or 'prawn' in normalized:
        from .shrimp_strategy import ShrimpFeedingStrategy

        return ShrimpFeedingStrategy()

    if normalized:
        from .fish_strategy import FishFeedingStrategy

        return FishFeedingStrategy()

    from .general_strategy import GeneralFeedingStrategy

    return GeneralFeedingStrategy()
