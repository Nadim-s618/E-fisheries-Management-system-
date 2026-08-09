export const DASHBOARD_NAV_ITEMS = [
  { id: 'water', label: 'Water Quality', icon: 'M12 2C8 6 4 9 4 13a8 8 0 0016 0c0-4-4-7-8-11z' },
  { id: 'feeding', label: 'Fish Feeding', icon: 'M3 12h18M3 6l9-3 9 3M3 18l9 3 9-3' },
  { id: 'health', label: 'Fish Health', icon: 'M12 21C7 17 3 13.5 3 9a5 5 0 0110 0 5 5 0 0110 0c0 4.5-4 8-9 12z' },
  { id: 'stock', label: 'Stock & Growth', icon: 'M3 20l4-8 4 4 4-6 4 10' },
  { id: 'weather', label: 'Weather', icon: 'M12 3v1m0 16v1M4.22 4.22l.7.7m12.16 12.16l.7.7M1 12h1m18 0h1M4.22 19.78l.7-.7M18.36 5.64l.7-.7M12 7a5 5 0 100 10A5 5 0 0012 7z' },
  { id: 'finance', label: 'Financials', icon: 'M12 2v20M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6' },
  { id: 'market', label: 'Market Bridge', icon: 'M3 6h18M3 12h18M3 18h12' },
  { id: 'analysis', label: 'Market Analysis', icon: 'M18 20V10M12 20V4M6 20v-6' },
];

export const DASHBOARD_ALERTS = [
  { pond: 'Purba Madhnagar', issue: 'High oxygen level' },
  { pond: 'Dighi', issue: 'Low pH level' },
];

export const DASHBOARD_STATS = [
  { label: 'Total Ponds', value: '5', sub: '4 healthy', accent: 'teal' },
  { label: 'Total Fish', value: '2,000', sub: 'across all ponds', accent: 'blue' },
  { label: 'Avg Temperature', value: '21.7°C', sub: 'within range', accent: 'amber' },
  { label: 'Avg Oxygen', value: '8.1 mg/L', sub: 'optimal', accent: 'green' },
];
//cd backend
//python manage.py runserver
