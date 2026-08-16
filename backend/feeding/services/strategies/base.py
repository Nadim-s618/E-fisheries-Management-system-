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
    if isinstance(species, (list, tuple, set)):
        species_names = [str(item or '').strip() for item in species if str(item or '').strip()]
        if len(species_names) > 1:
            from .mixed_strategy import MixedFishFeedingStrategy

            return MixedFishFeedingStrategy()
        species = species_names[0] if species_names else None

    normalized = str(species or '').strip().lower()

    if normalized in {'mixed', 'mixed fish', 'mix fish', 'mix'}:
        from .mixed_strategy import MixedFishFeedingStrategy

        return MixedFishFeedingStrategy()

    if 'shrimp' in normalized or 'prawn' in normalized:
        from .shrimp_strategy import ShrimpFeedingStrategy

        return ShrimpFeedingStrategy()

    if normalized in {'tilapia', 'monosex tilapia', 'nile tilapia'}:
        from .tilapia_strategy import TilapiaFeedingStrategy

        return TilapiaFeedingStrategy()

    if normalized in {
        'rohu', 'rui', 'catla', 'mrigal', 'carp', 'common carp',
        'silver carp', 'grass carp', 'bighead carp',
    }:
        from .carp_strategy import CarpFeedingStrategy

        return CarpFeedingStrategy()

    if normalized in {'pangasius', 'pangas', 'basa', 'catfish', 'shingi', 'magur'}:
        from .pangasius_strategy import PangasiusFeedingStrategy

        return PangasiusFeedingStrategy()

    if normalized:
        from .fish_strategy import FishFeedingStrategy

        return FishFeedingStrategy()

    from .general_strategy import GeneralFeedingStrategy

    return GeneralFeedingStrategy()
