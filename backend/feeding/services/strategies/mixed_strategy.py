from .fish_strategy import FishFeedingStrategy


class MixedFishFeedingStrategy(FishFeedingStrategy):
    """Shared schedule for ponds containing more than one species."""

    name = 'mixed'
