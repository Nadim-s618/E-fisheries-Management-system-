export const marketProfile = { can_sell: true };

export const marketBridgePonds = [
  { id: 1, name: 'North Pond' },
];

export const marketBridgeStocks = [
  { id: 101, batch_name: 'Tilapia Batch A', species: 'Tilapia', current_quantity: 1200 },
];

export const marketListings = [
  {
    id: 201,
    title: 'Fresh Tilapia from North Pond',
    status: 'active',
    species: 'Tilapia',
    quantity_kg: 100,
    available_quantity_kg: 75,
    unit_price: 260,
    description: 'Healthy table-size fish.',
  },
  {
    id: 202,
    title: 'Sold Out Rui',
    status: 'sold_out',
    species: 'Rui',
    quantity_kg: 50,
    available_quantity_kg: 0,
    unit_price: 300,
    description: '',
  },
];

export const marketOrders = [
  {
    id: 301,
    seller: 7,
    listing_species: 'Tilapia',
    listing_title: 'Fresh Tilapia from North Pond',
    listing_location: 'Dhaka',
    quantity_kg: 10,
    unit_price: 260,
    total_price: 2600,
    status: 'pending',
    buyer_name: 'buyer@example.com',
    buyer_username: 'buyer01',
    buyer_full_name: 'Test Buyer',
    buyer_email: 'buyer@example.com',
    buyer_contact_number: '01700000000',
    buyer_address: 'Dhaka, Bangladesh',
    buyer_note: 'Please call before delivery.',
    seller_name: 'Farm Seller',
    transaction_code: 'TXN-301',
  },
];
