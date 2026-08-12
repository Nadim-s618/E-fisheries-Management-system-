from django.test import SimpleTestCase

from market_bridge.services import DIVISION_ALIASES, infer_division


class MarketBridgeServiceUnitTests(SimpleTestCase):
    def test_infer_division_accepts_known_division_names(self):
        self.assertEqual(infer_division('Farm Road, Dhaka'), 'Dhaka')
        self.assertEqual(infer_division('Chittagong wholesale market'), 'Chattogram')
        self.assertEqual(infer_division('Rangpur'), 'Rangpur')

    def test_infer_division_is_case_insensitive_and_handles_empty_location(self):
        self.assertEqual(infer_division('KHULNA fish market'), 'Khulna')
        self.assertEqual(infer_division(''), '')
        self.assertEqual(infer_division(None), '')

    def test_infer_division_returns_empty_for_unknown_location(self):
        self.assertEqual(infer_division('Coxs Bazar'), '')

    def test_division_aliases_map_to_supported_divisions(self):
        self.assertEqual(DIVISION_ALIASES['chittagong'], 'Chattogram')
        self.assertEqual(len(set(DIVISION_ALIASES.values())), 8)
