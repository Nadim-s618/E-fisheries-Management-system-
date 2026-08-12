from django.test import SimpleTestCase

from water_quality.services.ai_advisor import (
    build_water_quality_prompt,
    get_fallback_advice,
    normalize_ai_advice,
    normalize_list,
)
from water_quality.services.notification_service import (
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    build_reason,
    get_priority,
)
from water_quality.utils.thresholds import STATUS_DANGER, STATUS_GOOD, STATUS_WARNING


class WaterQualityAdvisorUnitTests(SimpleTestCase):
    def test_fallback_advice_is_positive_when_all_parameters_are_good(self):
        analysis = {
            'overall_status': STATUS_GOOD,
            'parameters': [{'parameter': 'temperature', 'status': STATUS_GOOD}],
        }

        advice = get_fallback_advice(analysis)

        self.assertEqual(advice['source'], 'fallback')
        self.assertFalse(advice['ai_enabled'])
        self.assertEqual(advice['emergency_actions'], [])
        self.assertEqual(advice['danger_parameter_solutions'], [])

    def test_fallback_advice_adds_emergency_actions_for_danger(self):
        analysis = {
            'overall_status': STATUS_DANGER,
            'parameters': [{'parameter': 'ammonia', 'status': STATUS_DANGER}],
        }

        advice = get_fallback_advice(analysis)

        self.assertIn('ammonia', advice['explanation'])
        self.assertTrue(advice['emergency_actions'])
        self.assertEqual(advice['danger_parameter_solutions'][0]['parameter'], 'ammonia')
        self.assertTrue(advice['danger_parameter_solutions'][0]['suggestions'])

    def test_normalize_list_keeps_clean_values(self):
        self.assertEqual(
            normalize_list(['  Aerate pond  ', '', None, 12], ['fallback']),
            ['Aerate pond', 'None', '12'],
        )

    def test_normalize_list_uses_fallback_for_invalid_input(self):
        fallback = ['Retest water']

        self.assertEqual(normalize_list('not a list', fallback), fallback)
        self.assertEqual(normalize_list([], fallback), fallback)

    def test_normalize_ai_advice_returns_gemini_response(self):
        fallback = get_fallback_advice({'overall_status': STATUS_GOOD, 'parameters': []})
        advice = normalize_ai_advice({
            'explanation': 'Water is stable.',
            'recommendations': ['Check oxygen'],
            'preventive_actions': ['Test daily'],
            'emergency_actions': [],
            'danger_parameter_solutions': [],
        }, fallback)

        self.assertEqual(advice['source'], 'gemini')
        self.assertTrue(advice['ai_enabled'])
        self.assertEqual(advice['recommendations'], ['Check oxygen'])

    def test_normalize_ai_advice_keeps_only_known_danger_solutions(self):
        fallback = get_fallback_advice({
            'overall_status': STATUS_DANGER,
            'parameters': [{'parameter': 'ammonia', 'value': 0.08, 'normal_range': '0-0.02 mg/L', 'status': STATUS_DANGER}],
        })

        advice = normalize_ai_advice({
            'danger_parameter_solutions': [
                {'parameter': 'ammonia', 'problem': 'Ammonia is unsafe.', 'suggestions': ['Aerate now.']},
                {'parameter': 'temperature', 'problem': 'Ignore this.', 'suggestions': ['Ignore this.']},
            ],
        }, fallback)

        self.assertEqual(advice['danger_parameter_solutions'], [{
            'parameter': 'ammonia',
            'problem': 'Ammonia is unsafe.',
            'suggestions': ['Aerate now.'],
        }])

    def test_prompt_contains_analysis_and_context(self):
        prompt = build_water_quality_prompt(
            {'overall_status': STATUS_WARNING, 'parameters': []},
            {'pond': {'name': 'North Pond'}},
        )

        self.assertIn('North Pond', prompt)
        self.assertIn('Warning', prompt)


class WaterQualityNotificationUnitTests(SimpleTestCase):
    def test_get_priority_maps_danger_and_warning(self):
        self.assertEqual(get_priority(STATUS_DANGER), PRIORITY_HIGH)
        self.assertEqual(get_priority(STATUS_WARNING), PRIORITY_MEDIUM)

    def test_get_priority_ignores_good_status(self):
        self.assertIsNone(get_priority(STATUS_GOOD))

    def test_build_reason_contains_parameter_status_value_and_range(self):
        reason = build_reason({
            'parameter': 'ammonia',
            'status': STATUS_DANGER,
            'value': 0.08,
            'normal_range': '0-0.02 mg/L',
        })

        self.assertEqual(
            reason,
            'ammonia is Danger. Current value is 0.08; normal range is 0-0.02 mg/L.',
        )
