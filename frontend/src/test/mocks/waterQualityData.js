export const waterQualityPonds = [
  { id: 1, name: 'North Pond' },
  { id: 2, name: 'South Pond' },
];

export const waterQualityDashboard = {
  overall_status: 'Warning',
  good_count: 5,
  warning_count: 2,
  danger_count: 1,
  parameter_cards: [
    {
      parameter: 'temperature',
      status: 'Good',
      current_value: 28,
      normal_range: '24–30 °C',
      trend: '↑',
      last_updated: '2026-08-13T10:00:00Z',
    },
    {
      parameter: 'ph',
      status: 'Warning',
      current_value: 7.5,
      normal_range: '6.5–8.5',
      trend: '→',
      last_updated: '2026-08-13T10:00:00Z',
    },
  ],
  ai_advice: {
    ai_enabled: false,
    explanation: 'Water quality is generally stable, but monitor pH closely.',
    recommendations: ['Improve water quality before the next feeding.'],
    preventive_actions: ['Check the pond each morning.'],
    emergency_actions: ['Increase aeration if dissolved oxygen falls.'],
    danger_parameter_solutions: [
      {
        parameter: 'ammonia',
        problem: 'Ammonia is above the safe range.',
        suggestions: ['Replace part of the pond water.'],
      },
    ],
  },
};

export const waterQualityHistory = {
  results: [
    { temperature: 27, ph: 7.2 },
    { temperature: 28, ph: 7.5 },
  ],
};

export const waterQualityReadings = [
  {
    id: 501,
    created_at: '2026-08-13T10:00:00Z',
    pond_name: 'North Pond',
    temperature: 28,
    ph: 7.5,
    dissolved_oxygen: 6,
    ammonia: 0.1,
    nitrite: 0.05,
    nitrate: 10,
    turbidity: 3,
    salinity: 0,
    water_level: 5,
    overall_status: 'Good',
  },
];

export const waterQualityComparison = {
  ponds: [
    {
      rank: 1,
      pond: { id: 1, name: 'North Pond' },
      overall_status: 'Good',
      danger_count: 0,
      warning_count: 1,
      good_count: 7,
      average_values: { temperature: 28, ph: 7.4, dissolved_oxygen: 6.2 },
    },
    {
      rank: 2,
      pond: { id: 2, name: 'South Pond' },
      overall_status: 'Warning',
      danger_count: 1,
      warning_count: 2,
      good_count: 5,
      average_values: { temperature: 29, ph: 7.1, dissolved_oxygen: 5.8 },
    },
  ],
};
