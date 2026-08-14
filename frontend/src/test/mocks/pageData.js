export const homepageData = {
  navLinks: ['Home', 'Features', 'Fish Store'],
  hero: {
    title: 'Manage smarter fisheries',
    accent: 'Grow better fish',
    eyebrow: 'Modern aquaculture',
    subtitle: 'Monitor every part of your fishery.',
  },
  stats: [{ label: 'Ponds managed', value: '500+' }],
  features: [{ title: 'Water quality', desc: 'Track water health.' }],
  cta: { title: 'Ready to grow?', subtitle: 'Start today.', buttonText: 'Get started' },
};

export const fishStoreListings = [
  {
    id: 1,
    title: 'Fresh Tilapia from North Pond',
    species: 'Tilapia',
    location: 'Dhaka',
    available_quantity_kg: 75,
    unit_price: 260,
    average_height_cm: 18,
    average_weight_g: 350,
  },
];

export const placedOrder = [{
  id: 101,
  transaction_code: 'MF-ABC123',
  listing_title: 'Fresh Tilapia from North Pond',
  listing_species: 'Tilapia',
  quantity_kg: 2,
  unit_price: 260,
  total_price: 520,
  status: 'pending',
  status_display: 'Pending',
}];

export const pagePonds = [
  { id: 1, name: 'North Pond', status: 'active' },
  { id: 2, name: 'South Pond', status: 'maintenance' },
];

export const pageNotifications = [
  { id: 1, pond_name: 'North Pond', parameter: 'pH', current_value: 6.2, priority: 'High', reason: 'pH is below the safe range.' },
];
