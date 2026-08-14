export const marketAnalysisDashboard = {
  as_of_date: '2026-08-14',
  price_source: 'Bangladesh Fish Market Authority',
  divisions: ['Dhaka', 'Chattogram', 'Rajshahi'],
  fish: ['Rui', 'Tilapia'],
  summary: {
    market_points: 4,
    average_price_today: 210,
    high_demand_count: 2,
    biggest_mover: {
      fish_name: 'Rui',
      division: 'Dhaka',
      change_percent: 12.5,
      direction: 'up',
    },
  },
  records: [
    {
      fish_name: 'Rui',
      division: 'Dhaka',
      today_price: 220,
      yesterday_price: 195,
      change_amount: 25,
      change_percent: 12.82,
      direction: 'up',
      demand_level: 'High',
      last_7_days: [
        { date: '2026-08-08', price: 190 },
        { date: '2026-08-14', price: 220 },
      ],
      next_7_days: [
        { date: '2026-08-15', predicted_price: 225 },
        { date: '2026-08-21', predicted_price: 235 },
      ],
    },
    {
      fish_name: 'Tilapia',
      division: 'Chattogram',
      today_price: 180,
      yesterday_price: 182,
      change_amount: -2,
      change_percent: -1.1,
      direction: 'down',
      demand_level: 'Medium',
      last_7_days: [{ date: '2026-08-14', price: 180 }],
      next_7_days: [{ date: '2026-08-15', predicted_price: 178 }],
    },
  ],
};
