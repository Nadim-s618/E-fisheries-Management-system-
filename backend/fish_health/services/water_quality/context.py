from water_quality.models import WaterQualityReading


def get_latest_water_quality_snapshot(pond):
    reading = (
        WaterQualityReading.objects
        .filter(pond=pond)
        .order_by('-created_at')
        .first()
    )

    if reading is None:
        return {}

    return {
        'id': reading.id,
        'temperature': reading.temperature,
        'ph': reading.ph,
        'dissolved_oxygen': reading.dissolved_oxygen,
        'ammonia': reading.ammonia,
        'nitrite': reading.nitrite,
        'nitrate': reading.nitrate,
        'turbidity': reading.turbidity,
        'salinity': reading.salinity,
        'water_level': reading.water_level,
        'overall_status': reading.overall_status,
        'created_at': reading.created_at.isoformat(),
    }


def get_water_quality_risk_notes(snapshot):
    if not snapshot:
        return []

    notes = []

    if snapshot.get('overall_status') in {'Warning', 'Danger'}:
        notes.append(f"Latest water quality is {snapshot['overall_status']}.")
    if snapshot.get('dissolved_oxygen') is not None and snapshot['dissolved_oxygen'] < 5:
        notes.append('Dissolved oxygen is low and may increase breathing stress.')
    if snapshot.get('ammonia') is not None and snapshot['ammonia'] > 0.5:
        notes.append('Ammonia is elevated and can damage gills.')
    if snapshot.get('nitrite') is not None and snapshot['nitrite'] > 0.3:
        notes.append('Nitrite is elevated and can reduce oxygen transport.')
    if snapshot.get('ph') is not None and (snapshot['ph'] < 6.5 or snapshot['ph'] > 8.5):
        notes.append('pH is outside the usual safe range.')
    if snapshot.get('temperature') is not None and snapshot['temperature'] > 32:
        notes.append('Water temperature is high, increasing oxygen demand.')

    return notes
