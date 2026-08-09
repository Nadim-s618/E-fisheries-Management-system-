from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.services.farm_advisor import build_fallback_advice, normalize_list, serialize
from core.services.gemini import GeminiError, extract_text, generate_text_response, strip_json_code_block


class CoreServiceUnitTests(SimpleTestCase):
    def test_normalize_list_keeps_non_empty_values_as_strings(self):
        self.assertEqual(normalize_list(['  Check water  ', 12, '', None]), ['Check water', '12', 'None'])
        self.assertEqual(normalize_list('not a list'), [])

    def test_serialize_converts_nested_decimal_and_dates(self):
        value = {
            'weight': Decimal('12.50'),
            'date': date(2026, 1, 15),
            'timestamp': datetime(2026, 1, 15, 10, 30),
            'items': [Decimal('2.00')],
        }

        self.assertEqual(serialize(value), {
            'weight': '12.50',
            'date': '2026-01-15',
            'timestamp': '2026-01-15T10:30:00',
            'items': ['2.00'],
        })

    def test_fallback_advice_reports_missing_water_and_stock(self):
        advice = build_fallback_advice({
            'water_quality': {},
            'fish_health': {},
            'stock': {'current_quantity': 0},
        })

        self.assertEqual(advice['source'], 'fallback')
        self.assertEqual(advice['priority'], 'Attention')
        self.assertIn('Water quality data is missing.', advice['risks'])
        self.assertIn('No active stock quantity is available.', advice['risks'])

    def test_strip_json_code_block_removes_markdown_wrapper(self):
        self.assertEqual(strip_json_code_block('```json\n{"ok": true}\n```'), '{"ok": true}')
        self.assertEqual(strip_json_code_block('{"ok": true}'), '{"ok": true}')

    def test_extract_text_joins_gemini_parts(self):
        response = {'candidates': [{'content': {'parts': [{'text': 'first '}, {'text': 'second'}]}}]}

        self.assertEqual(extract_text(response), 'first second')

    def test_extract_text_rejects_missing_candidates(self):
        with self.assertRaisesRegex(GeminiError, 'no candidates'):
            extract_text({'candidates': []})

    @override_settings(GOOGLE_API_KEY='', GEMINI_API_KEY='')
    def test_generate_text_response_requires_api_key(self):
        with self.assertRaisesRegex(GeminiError, 'not configured'):
            generate_text_response('Give advice')

    @patch('core.services.farm_advisor.is_gemini_configured', return_value=False)
    def test_gemini_disabled_returns_fallback_advice(self, configured):
        from core.services.farm_advisor import get_farm_advice

        context = {'water_quality': {}, 'fish_health': {}, 'stock': {'current_quantity': 0}}
        with patch('core.services.farm_advisor.build_farm_context', return_value=context):
            advice = get_farm_advice(object())

        self.assertFalse(advice['ai_enabled'])
        self.assertEqual(advice['source'], 'fallback')
        configured.assert_called_once_with()
