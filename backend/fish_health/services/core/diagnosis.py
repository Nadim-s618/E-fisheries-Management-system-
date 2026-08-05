import json
import re

from core.services.gemini import GeminiError, generate_text_response, is_gemini_configured
from fish_health.models import DiseaseProfile, HealthRecord
from fish_health.services.water_quality.context import get_water_quality_risk_notes
from fish_health.services.weather.context import get_weather_risk_notes


SEVERITY_SCORE = {
    DiseaseProfile.RiskLevel.LOW: 1,
    DiseaseProfile.RiskLevel.MODERATE: 2,
    DiseaseProfile.RiskLevel.HIGH: 3,
    DiseaseProfile.RiskLevel.CRITICAL: 4,
}

HIGH_RISK_TERMS = {
    'sudden death',
    'gasping at surface',
    'red gills',
    'rapid breathing',
    'skin ulcers',
    'morning mortality',
}


def diagnose_health_record(record):
    possible_diseases = match_possible_diseases(
        species=record.species,
        symptoms=record.symptoms,
        symptom_notes=record.symptom_notes,
        water_quality_snapshot=record.water_quality_snapshot,
        weather_snapshot=record.weather_snapshot,
    )
    recommendation = build_ai_recommendation(record, possible_diseases)
    severity = calculate_record_severity(record, possible_diseases)

    record.possible_diseases = possible_diseases
    record.ai_recommendation = recommendation
    record.severity = severity
    record.save(update_fields=[
        'possible_diseases',
        'ai_recommendation',
        'severity',
        'updated_at',
    ])

    return record


def match_possible_diseases(*, species, symptoms, symptom_notes, water_quality_snapshot, weather_snapshot):
    symptom_terms = normalize_terms(symptoms)
    text_terms = tokenize(symptom_notes)
    species_value = (species or '').strip().lower()
    matches = []

    for disease in DiseaseProfile.objects.filter(is_active=True):
        disease_symptoms = normalize_terms(disease.symptoms)
        disease_species = normalize_terms(disease.species)

        if disease_species and species_value and species_value not in disease_species:
            continue

        direct_matches = sorted(symptom_terms.intersection(disease_symptoms))
        text_matches = sorted(
            symptom
            for symptom in disease_symptoms
            if symptom in (symptom_notes or '').lower()
            or any(token in text_terms for token in symptom.split())
        )
        matched_symptoms = sorted(set(direct_matches + text_matches))
        environment_matches = find_environment_matches(
            disease.environmental_triggers,
            water_quality_snapshot,
            weather_snapshot,
        )

        score = (len(matched_symptoms) * 28) + (len(environment_matches) * 8)
        if disease.risk_level in {DiseaseProfile.RiskLevel.HIGH, DiseaseProfile.RiskLevel.CRITICAL}:
            score += 6

        if not matched_symptoms and not environment_matches:
            continue

        confidence = min(95, max(18, score))
        matches.append({
            'id': disease.id,
            'name': disease.name,
            'confidence': confidence,
            'risk_level': disease.risk_level,
            'matched_symptoms': matched_symptoms,
            'environment_matches': environment_matches,
            'description': disease.description,
            'recommended_treatments': disease.recommended_treatments,
            'treatment_protocols': disease.treatment_protocols,
            'maintenance_actions': disease.maintenance_actions,
            'prevention': disease.prevention,
        })

    return sorted(matches, key=lambda item: (-item['confidence'], item['name']))[:5]


def calculate_record_severity(record, possible_diseases):
    selected_terms = normalize_terms(record.symptoms)
    note_text = (record.symptom_notes or '').lower()
    mortality_count = record.mortality_count or 0

    if mortality_count > 0:
        return HealthRecord.Severity.CRITICAL

    if selected_terms.intersection(HIGH_RISK_TERMS) or any(term in note_text for term in HIGH_RISK_TERMS):
        return HealthRecord.Severity.HIGH

    top_risk = max(
        [SEVERITY_SCORE.get(item['risk_level'], 1) for item in possible_diseases],
        default=1,
    )

    if top_risk >= 4:
        return HealthRecord.Severity.CRITICAL
    if top_risk == 3:
        return HealthRecord.Severity.HIGH
    if top_risk == 2:
        return HealthRecord.Severity.MODERATE
    return HealthRecord.Severity.LOW


def build_ai_recommendation(record, possible_diseases):
    water_notes = get_water_quality_risk_notes(record.water_quality_snapshot)
    weather_notes = get_weather_risk_notes(record.weather_snapshot)
    lines = []

    if possible_diseases:
        top = possible_diseases[0]
        lines.append(
            f"Most likely issue: {top['name']} ({top['confidence']}% match, {top['risk_level']} risk)."
        )
        if top['matched_symptoms']:
            lines.append(f"Matched symptoms: {', '.join(top['matched_symptoms'])}.")
        if top['recommended_treatments']:
            lines.append(f"Immediate action: {top['recommended_treatments'][0]}")
        if top.get('treatment_protocols'):
            protocol = top['treatment_protocols'][0]
            medicine = protocol.get('medicine') or 'Supportive treatment'
            dosage = protocol.get('dosage') or 'Follow product label and specialist guidance'
            cost = protocol.get('estimated_cost') or 'Cost depends on pond size and local price'
            lines.append(f"Recommended treatment option: {medicine}. Dosage: {dosage}. Estimated cost: {cost}.")
        if top.get('maintenance_actions'):
            lines.append(f"Maintenance: {top['maintenance_actions'][0]}")
    else:
        lines.append('No strong disease match found. Keep monitoring and add more symptom detail after inspection.')

    if record.mortality_count:
        lines.append('Mortality was recorded, so isolate affected fish where possible and escalate quickly.')
    if record.affected_count:
        lines.append(f"{record.affected_count} fish are affected; compare this with total stock before treatment.")

    lines.extend(water_notes)
    lines.extend(weather_notes)

    if not water_notes:
        lines.append('Latest water quality did not add a clear disease trigger, but retesting is recommended.')
    if not weather_notes:
        lines.append('Latest weather data does not indicate a major disease trigger.')

    lines.append('Confirm diagnosis before applying medicine; use approved aquaculture treatments and local dosage guidance.')
    fallback = ' '.join(lines)
    return get_gemini_health_recommendation(
        record=record,
        possible_diseases=possible_diseases,
        water_notes=water_notes,
        weather_notes=weather_notes,
        fallback=fallback,
    )


def get_gemini_health_recommendation(*, record, possible_diseases, water_notes, weather_notes, fallback):
    if not is_gemini_configured():
        return fallback

    try:
        recommendation = generate_text_response(
            build_health_prompt(record, possible_diseases, water_notes, weather_notes, fallback),
            temperature=0.2,
            max_output_tokens=750,
        )
    except GeminiError:
        return fallback

    recommendation = ' '.join(recommendation.split())
    return recommendation or fallback


def build_health_prompt(record, possible_diseases, water_notes, weather_notes, fallback):
    prompt_data = {
        'health_record': {
            'pond': record.pond.name,
            'species': record.species,
            'observed_at': record.observed_at.isoformat() if record.observed_at else None,
            'symptoms': record.symptoms,
            'symptom_notes': record.symptom_notes,
            'abnormal_behavior': record.abnormal_behavior,
            'affected_count': record.affected_count,
            'mortality_count': record.mortality_count,
            'severity': record.severity,
        },
        'possible_diseases': possible_diseases,
        'water_quality_snapshot': record.water_quality_snapshot,
        'weather_snapshot': record.weather_snapshot,
        'water_risk_notes': water_notes,
        'weather_risk_notes': weather_notes,
        'rule_based_recommendation': fallback,
    }

    return (
        'You are an aquaculture fish health advisor. Use English only. '
        'Use the rule-based disease matches and environmental context as evidence. '
        'Write one concise recommendation paragraph for the farmer. Include immediate actions, '
        'monitoring, treatment caution, and when to escalate to a local aquaculture expert. '
        'Do not claim a confirmed diagnosis. Do not invent unavailable lab results or exact drug dosages. '
        f'Data: {json.dumps(prompt_data)}'
    )


def find_environment_matches(triggers, water_quality_snapshot, weather_snapshot):
    trigger_terms = normalize_terms(triggers)
    matches = []

    if 'low dissolved oxygen' in trigger_terms and water_quality_snapshot.get('dissolved_oxygen') is not None:
        if water_quality_snapshot['dissolved_oxygen'] < 5:
            matches.append('low dissolved oxygen')
    if 'high ammonia' in trigger_terms and water_quality_snapshot.get('ammonia') is not None:
        if water_quality_snapshot['ammonia'] > 0.5:
            matches.append('high ammonia')
    if 'high ph' in trigger_terms and water_quality_snapshot.get('ph') is not None:
        if water_quality_snapshot['ph'] > 8.5:
            matches.append('high pH')
    if 'temperature fluctuation' in trigger_terms and weather_snapshot.get('rainfall_probability') is not None:
        if weather_snapshot['rainfall_probability'] >= 70:
            matches.append('weather-driven temperature fluctuation')
    if 'warm water' in trigger_terms and water_quality_snapshot.get('temperature') is not None:
        if water_quality_snapshot['temperature'] > 30:
            matches.append('warm water')
    if 'cloudy weather' in trigger_terms and weather_snapshot.get('disease_risk') in {'Moderate', 'High'}:
        matches.append('weather disease risk')

    return matches


def normalize_terms(values):
    return {
        str(value).strip().lower()
        for value in (values or [])
        if str(value).strip()
    }


def tokenize(value):
    return set(re.findall(r'[a-z0-9]+', (value or '').lower()))
