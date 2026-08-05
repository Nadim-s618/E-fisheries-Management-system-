import json

from core.services.gemini import GeminiError, generate_json_response, is_gemini_configured


def get_water_quality_advice(analysis, context=None):
    fallback = get_fallback_advice(analysis)

    if not is_gemini_configured():
        return fallback

    try:
        ai_advice = generate_json_response(build_water_quality_prompt(analysis, context or {}))
    except (GeminiError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return fallback

    return normalize_ai_advice(ai_advice, fallback)


def build_water_quality_prompt(analysis, context):
    prompt_data = {
        'overall_status': analysis.get('overall_status'),
        'parameters': [
            {
                'parameter': parameter.get('parameter'),
                'value': parameter.get('value'),
                'normal_range': parameter.get('normal_range'),
                'status': parameter.get('status'),
            }
            for parameter in analysis.get('parameters', [])
        ],
        'context': context,
    }

    return (
        'You are advising a fish farmer about pond water quality. '
        'Use English only. Use the rule-based statuses exactly as given; do not invent safer statuses. '
        'Consider pond, stock, weather, and recent history context when present. '
        'Keep advice practical for small to medium aquaculture ponds. '
        'Return JSON with keys: explanation, recommendations, preventive_actions, emergency_actions. '
        'recommendations, preventive_actions, and emergency_actions must be arrays of short practical strings. '
        f'Data: {json.dumps(prompt_data)}'
    )


def normalize_ai_advice(ai_advice, fallback):
    return {
        'source': 'gemini',
        'ai_enabled': True,
        'explanation': ai_advice.get('explanation') or fallback['explanation'],
        'recommendations': normalize_list(
            ai_advice.get('recommendations'),
            fallback['recommendations'],
        ),
        'preventive_actions': normalize_list(
            ai_advice.get('preventive_actions'),
            fallback['preventive_actions'],
        ),
        'emergency_actions': normalize_list(
            ai_advice.get('emergency_actions'),
            fallback['emergency_actions'],
        ),
    }


def normalize_list(value, fallback):
    if not isinstance(value, list):
        return fallback

    cleaned_items = [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]

    return cleaned_items or fallback


def get_fallback_advice(analysis):
    overall_status = analysis.get('overall_status', 'Good')
    risky_parameters = [
        parameter
        for parameter in analysis.get('parameters', [])
        if parameter.get('status') in {'Warning', 'Danger'}
    ]

    if not risky_parameters:
        return {
            'source': 'fallback',
            'ai_enabled': False,
            'explanation': 'All measured water quality parameters are within acceptable ranges.',
            'recommendations': [
                'Continue routine water quality monitoring.',
                'Keep feeding, aeration, and water exchange records updated.',
            ],
            'preventive_actions': [
                'Test water at the same time of day for consistent records.',
                'Avoid sudden changes in feeding, stocking density, or water exchange.',
            ],
            'emergency_actions': [],
        }

    risky_names = ', '.join(
        parameter.get('parameter', 'unknown parameter')
        for parameter in risky_parameters
    )
    emergency_actions = []

    if overall_status == 'Danger':
        emergency_actions = [
            'Increase aeration immediately if fish show stress.',
            'Reduce or stop feeding until the risky values improve.',
            'Prepare partial water exchange if toxic compounds or oxygen stress are present.',
        ]

    return {
        'source': 'fallback',
        'ai_enabled': False,
        'explanation': f'Water quality needs attention because these parameters are outside normal range: {risky_names}.',
        'recommendations': [
            'Retest the risky parameters to confirm the reading.',
            'Improve aeration and remove uneaten feed or organic waste.',
            'Use partial water exchange when chemical levels remain unsafe.',
        ],
        'preventive_actions': [
            'Maintain regular testing for temperature, pH, oxygen, nitrogen compounds, and turbidity.',
            'Avoid overfeeding and remove sludge buildup from the pond bottom.',
            'Keep stocking density within pond capacity.',
        ],
        'emergency_actions': emergency_actions,
    }
