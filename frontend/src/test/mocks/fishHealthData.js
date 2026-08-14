export const fishHealthPonds = [
  { id: 1, name: 'North Pond', location: 'Dhaka' },
  { id: 2, name: 'South Pond', location: 'Khulna' },
];

export const fishStocks = [
  { id: 101, batch_name: 'Tilapia Batch A', species: 'Tilapia' },
];

export const healthRecord = {
  id: 201,
  observed_at: '2026-08-14T08:00:00Z',
  pond_name: 'North Pond',
  fish_stock_name: 'Tilapia Batch A',
  symptoms: ['white spots', 'reduced feeding'],
  severity: 'High',
  status: 'Open',
  ai_recommendation: 'Isolate affected fish and improve water quality.',
  possible_diseases: [
    {
      name: 'Ich',
      confidence: 92,
      risk_level: 'High',
      description: 'A parasitic infection commonly seen as white spots.',
      matched_symptoms: ['white spots'],
      treatment_protocols: [
        {
          medicine: 'Malachite Green',
          dosage: '0.1 mg/L',
          duration: '3 days',
          estimated_cost: 'TK 500',
          maintenance: 'Increase aeration',
        },
      ],
      maintenance_actions: ['Monitor fish daily'],
    },
  ],
};

export const fishHealthDashboard = {
  summary: {
    total_records: 12,
    active_cases: 3,
    critical_cases: 1,
    active_treatments: 2,
    disease_library_count: 15,
    unread_health_alerts: 1,
  },
  water_quality: {
    snapshot: { temperature: 28, dissolved_oxygen: 5.5 },
    risk_notes: ['Oxygen is below the preferred range'],
  },
  weather: {
    snapshot: { temperature: 30, humidity: 75 },
    risk_notes: [],
  },
  latest_records: [healthRecord],
};

export const diseases = [
  {
    id: 301,
    name: 'Ich',
    risk_level: 'High',
    description: 'A parasitic infection commonly seen as white spots.',
    symptoms: ['white spots', 'rubbing body'],
    recommended_treatments: ['Increase water temperature', 'Use parasite treatment'],
    treatment_protocols: [{ medicine: 'Malachite Green', dosage: '0.1 mg/L' }],
    maintenance_actions: ['Monitor fish daily'],
    prevention: ['Quarantine new fish', 'Maintain water quality'],
  },
];

export const treatments = [
  {
    id: 401,
    medicine_name: 'Malachite Green',
    dosage: '0.1 mg/L',
    status: 'Active',
    start_date: '2026-08-14',
    end_date: '2026-08-17',
    cost: 500,
    tracking: [],
  },
];

export const recommendation = {
  recommendation: 'Increase aeration and monitor affected fish twice daily.',
  record: healthRecord,
};

export const alerts = [
  {
    id: 501,
    pond_name: 'North Pond',
    reason: 'High severity fish health case detected',
    priority: 'High',
    is_read: false,
    created_at: '2026-08-14T09:00:00Z',
  },
];
