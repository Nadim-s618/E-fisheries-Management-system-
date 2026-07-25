import json
import os
import urllib.error
import urllib.request


GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_URL = (
    'https://generativelanguage.googleapis.com/v1beta/models/'
    f'{GEMINI_MODEL}:generateContent'
)


def get_water_quality_advice(analysis):
    fallback = get_fallback_advice(analysis)
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        return fallback

    try:
        ai_advice = request_gemini_advice(api_key, analysis)
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return fallback

    return normalize_ai_advice(ai_advice, fallback)


def request_gemini_advice(api_key, analysis):
    request = urllib.request.Request(
        f'{GEMINI_URL}?key={api_key}',
        data=json.dumps(build_gemini_payload(analysis)).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        response_body = json.loads(response.read().decode('utf-8'))

    text = extract_gemini_text(response_body)
    return json.loads(strip_json_code_block(text))


def build_gemini_payload(analysis):
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
    }

    prompt = (
        'You are advising a fish farmer about pond water quality. '
        'Do not decide whether water is good or bad; use only the given statuses. '
        'Return JSON with keys: explanation, recommendations, preventive_actions, emergency_actions. '
        'Each action key must contain an array of short practical strings. '
        f'Data: {json.dumps(prompt_data)}'
    )

    return {
        'contents': [
            {
                'parts': [
                    {'text': prompt},
                ],
            },
        ],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 500,
            'responseMimeType': 'application/json',
        },
    }


def extract_gemini_text(response_body):
    candidates = response_body.get('candidates') or []
    parts = candidates[0]['content'].get('parts') or []
    return ''.join(part.get('text', '') for part in parts)


def strip_json_code_block(text):
    cleaned_text = text.strip()

    if cleaned_text.startswith('```json'):
        return cleaned_text.removeprefix('```json').removesuffix('```').strip()

    if cleaned_text.startswith('```'):
        return cleaned_text.removeprefix('```').removesuffix('```').strip()

    return cleaned_text


def normalize_ai_advice(ai_advice, fallback):
    return {
        'source': 'gemini',
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
