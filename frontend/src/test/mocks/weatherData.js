export const weatherPonds = [
  { id: 1, name: 'North Pond', location: 'Natore' },
  { id: 2, name: 'South Pond', location: 'Rajshahi' },
];

export const weatherDashboard = {
  stale: false,
  source_error: null,
  report: {
    pond_name: 'North Pond',
    resolved_location: 'Natore, Rajshahi, BD',
    air_temperature: 28,
    weather_code: 0,
    humidity: 70,
    rainfall_probability: 20,
    wind_speed: 8,
    uv_index: 5,
    cloud_cover: 30,
    atmospheric_pressure: 1012,
    fish_weather_risk: 'Low',
    disease_risk: 'Moderate',
    pond_impact: { summary: 'Low impact on pond operations.' },
    feeding_recommendation: [{ status: 'ok', text: 'Feed at 6 AM.' }],
    do_prediction: { morning: 7.8, night: 6.5, unit: 'mg/L', action: 'Aeration is not currently required.' },
    rain_impact: { ph: 'No significant change', turbidity: 'Low', overflow: 'Low' },
    alerts: [{ level: 'ok', text: 'No bad weather warning.' }],
    forecast: [
      { time: '2026-08-14T12:00:00Z', air_temperature: 29, rainfall_probability: 25 },
    ],
    updated_at: '2026-08-14T06:00:00Z',
    source: 'OpenWeather',
    source_url: 'https://openweathermap.org/api',
  },
};

export const southWeatherDashboard = {
  ...weatherDashboard,
  report: {
    ...weatherDashboard.report,
    pond_name: 'South Pond',
    resolved_location: 'Rajshahi, BD',
    air_temperature: 31,
  },
};
