export const stockGrowthPonds = [
  { id: 1, name: 'North Pond', location: 'Dhaka', stocking_capacity: 5000 },
];

export const stockBatch = {
  id: 21,
  species: 'Tilapia',
  batch_name: 'Tilapia Batch A',
  stocking_date: '2026-08-01',
  initial_quantity: 1000,
  current_quantity: 950,
  initial_average_weight_g: 20,
  status: 'active',
  notes: 'Healthy batch',
  growth_records: [],
  growth_analysis: {
    estimated_biomass_kg: 28.5,
    latest_average_weight_g: 30,
    daily_growth_rate_g: 0.5,
    survival_rate_percent: 95,
    feed_conversion_ratio: 1.4,
    growth_records_count: 1,
  },
};

export const growthRecord = {
  id: 31,
  recorded_date: '2026-08-14',
  sample_count: 20,
  average_weight_g: 32,
  average_length_cm: 12,
  mortality_count: 2,
  feed_used_kg: 4,
  notes: 'Good growth',
};
