export const feedingPonds = [
  { id: 1, name: 'North Pond', location: 'Dhaka', stocking_capacity: 5000 },
  { id: 2, name: 'South Pond', location: 'Khulna', stocking_capacity: 3500 },
];

export const feedingRecommendation = {
  id: 21,
  pond_name: 'North Pond',
  status: 'draft',
  recommended_feed_kg: 12.5,
  feed_type: 'Floating Feed 32%',
  price_per_kg: 135,
  estimated_cost: 1687.5,
  meals: 2,
  schedule: [
    { meal_number: 1, label: 'Morning', time: '08:00', feed_kg: 6.25 },
    { meal_number: 2, label: 'Evening', time: '16:30', feed_kg: 6.25 },
  ],
  reasons: ['Based on current biomass'],
  ai_advice: {
    ai_enabled: true,
    explanation: 'Feed consistently to support healthy growth.',
    recommendations: ['Check feed response after each meal'],
    cautions: ['Avoid overfeeding'],
  },
};

export const activePlan = {
  recommended_feed_kg: 12.5,
  sessions: [
    {
      id: 101,
      meal_number: 1,
      status: 'pending',
      scheduled_at: '2026-08-14T08:00:00Z',
      planned_feed_kg: 6.25,
    },
    {
      id: 102,
      meal_number: 2,
      status: 'completed',
      scheduled_at: '2026-08-14T16:30:00Z',
      planned_feed_kg: 6.25,
      actual_feed_kg: 6,
    },
  ],
};

export const feedingHistory = [
  {
    id: 301,
    recommendation_date: '2026-08-13',
    pond_name: 'North Pond',
    recommended_feed_kg: 11,
    estimated_cost: 1485,
    computed_status: 'Completed',
    status: 'completed',
  },
];
