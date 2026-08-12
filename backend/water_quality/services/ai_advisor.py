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
    danger_parameters = [
        {
            'parameter': parameter.get('parameter'),
            'value': parameter.get('value'),
            'normal_range': parameter.get('normal_range'),
        }
        for parameter in analysis.get('parameters', [])
        if parameter.get('status') == 'Danger'
    ]
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
        'danger_parameters': danger_parameters,
    }

    return (
        'You are advising a fish farmer about pond water quality. '
        'Use English only. Use the rule-based statuses exactly as given; do not invent safer statuses. '
        'Consider pond, stock, weather, and recent history context when present. '
        'Keep advice practical for small to medium aquaculture ponds. '
        'Return JSON with keys: explanation, recommendations, preventive_actions, emergency_actions, danger_parameter_solutions. '
        'recommendations, preventive_actions, and emergency_actions must be arrays of short practical strings. '
        'danger_parameter_solutions must be an array. Include exactly one object for every item in danger_parameters, '
        'and no objects for parameters that are not Danger. Each object must have parameter, problem, and suggestions keys; '
        'suggestions must be an array of 2-4 short, practical actions that can improve that parameter. '
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
        'danger_parameter_solutions': normalize_danger_solutions(
            ai_advice.get('danger_parameter_solutions'),
            fallback['danger_parameter_solutions'],
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


def normalize_danger_solutions(value, fallback):
    if not isinstance(value, list):
        return fallback

    fallback_by_parameter = {
        item['parameter']: item
        for item in fallback
    }
    solutions = []

    for item in value:
        if not isinstance(item, dict):
            continue

        parameter = str(item.get('parameter', '')).strip()
        fallback_item = fallback_by_parameter.get(parameter)
        if not fallback_item:
            continue

        suggestions = normalize_list(item.get('suggestions'), fallback_item['suggestions'])
        solutions.append({
            'parameter': parameter,
            'problem': str(item.get('problem', '')).strip() or fallback_item['problem'],
            'suggestions': suggestions,
        })

    return solutions or fallback


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
            'danger_parameter_solutions': [],
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
        'danger_parameter_solutions': [
            get_fallback_danger_solution(parameter)
            for parameter in risky_parameters
            if parameter.get('status') == 'Danger'
        ],
    }


def get_fallback_danger_solution(parameter):
    name = parameter.get('parameter', 'water quality parameter')
    value = parameter.get('value')
    normal_range = parameter.get('normal_range', 'the normal range')
    solution_map = {
        'temperature': [
            'Provide shade and add fresh water gradually when the pond is too warm.',
            'Avoid handling fish during the hottest part of the day.',
            'Increase aeration because warm water holds less oxygen.',
        ],
        'ph': [
            'Stop sudden chemical additions and retest before correcting pH.',
            'Use agricultural lime only for low pH, in small measured doses.',
            'Use partial water exchange if pH remains very high or very low.',
        ],
        'dissolved_oxygen': [
            'Run aerators immediately, especially before sunrise.',
            'Stop feeding temporarily and remove decomposing feed or waste.',
            'Use a partial water exchange if fish continue gasping at the surface.',
        ],
        'ammonia': [
            'Stop or sharply reduce feeding and remove uneaten feed.',
            'Increase aeration and perform a gradual partial water exchange.',
            'Remove sludge and check stocking density after the emergency is stable.',
        ],
        'nitrite': [
            'Reduce feeding and increase aeration immediately.',
            'Replace part of the water gradually with clean, conditioned water.',
            'Check filtration or biofilter performance and remove organic waste.',
        ],
        'nitrate': [
            'Perform regular partial water exchanges until nitrate falls.',
            'Reduce overfeeding and remove sludge or decaying vegetation.',
            'Support biofiltration with adequate aeration and maintenance.',
        ],
        'turbidity': [
            'Reduce feeding and stop activities that disturb the pond bottom.',
            'Remove suspended organic waste and improve filtration where available.',
            'Exchange water gradually if visibility does not improve after retesting.',
        ],
        'salinity': [
            'Correct salinity gradually with partial water changes to avoid fish shock.',
            'Check the water source and avoid adding salt until the reading is confirmed.',
            'Monitor fish behaviour and retest after each gradual adjustment.',
        ],
        'water_level': [
            'Restore the water level gradually with a safe, clean water source.',
            'Check for leaks, overflow, or pump issues before refilling.',
            'Maintain stable depth to reduce temperature and oxygen stress.',
        ],
    }

    return {
        'parameter': name,
        'problem': f'{name.replace("_", " ").title()} is {value}; the normal range is {normal_range}.',
        'suggestions': solution_map.get(name, [
            'Retest the reading to confirm it before making a major correction.',
            'Adjust water conditions gradually and monitor fish behaviour closely.',
            'Consult a local aquaculture specialist if fish show severe stress.',
        ]),
    }
