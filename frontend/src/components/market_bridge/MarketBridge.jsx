import { useEffect, useMemo, useState } from 'react';

import {
  acceptMarketOrder,
  cancelMarketOrder,
  completeMarketOrder,
  createMarketListing,
  createMarketOrder,
  getMarketListings,
  getMarketOrders,
  getMarketPriceRecommendation,
  getMarketProfile,
  getPondStocks,
  getPonds,
  rejectMarketOrder,
  updateMarketProfile,
} from '../../lib/api';
import { useAuth } from '../../context/useAuth';
import './MarketBridge.css';

const TABS = [
  { id: 'store', label: 'Store' },
  { id: 'sell', label: 'Sell' },
  { id: 'orders', label: 'Orders' },
];

const EMPTY_FORM = {
  source_type: 'manual',
  fish_stock: '',
  species: '',
  title: '',
  quantity_kg: '',
  unit_price: '',
  suggested_price: '',
  location: '',
  available_from: '',
  description: '',
  photo: null,
};

function money(value) {
  if (value === null || value === undefined || value === '') return 'BDT --';
  return `BDT ${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function number(value, suffix = '') {
  if (value === null || value === undefined || value === '') return '--';
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
}

function dateLabel(value) {
  if (!value) return 'Ready now';
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    .format(new Date(`${value}T00:00:00`));
}

function StatusBadge({ status }) {
  return <span className={`mb-badge mb-badge-${status}`}>{status.replace('_', ' ')}</span>;
}

function StatePanel({ type = 'empty', children }) {
  return <div className={`mb-state mb-state-${type}`}>{children}</div>;
}

function ListingCard({ listing, currentUserId, onOrder }) {
  const isOwnListing = listing.seller === currentUserId;

  return (
    <article className="mb-listing-card">
      <div className="mb-listing-photo">
        {listing.photo_url ? (
          <img src={listing.photo_url} alt={listing.title} />
        ) : (
          <span>{listing.species?.slice(0, 2).toUpperCase() || 'FS'}</span>
        )}
      </div>
      <div className="mb-listing-body">
        <div className="mb-card-top">
          <div>
            <span>{listing.species}</span>
            <h3>{listing.title}</h3>
          </div>
          <StatusBadge status={listing.status} />
        </div>
        <p>{listing.location}</p>
        <div className="mb-listing-metrics">
          <strong>{money(listing.unit_price)} / kg</strong>
          <span>{number(listing.available_quantity_kg, ' kg')} available</span>
          <span>{dateLabel(listing.available_from)}</span>
        </div>
        <div className="mb-card-bottom">
          <small>Seller: {listing.seller_name}</small>
          <button type="button" className="mb-btn mb-btn-primary" disabled={isOwnListing} onClick={() => onOrder(listing)}>
            Request order
          </button>
        </div>
      </div>
    </article>
  );
}

function OrderRow({ order, currentUserId, onAction }) {
  const isSeller = order.seller === currentUserId;
  const isBuyer = order.buyer === currentUserId;

  return (
    <article className="mb-order-row">
      <div>
        <span>{order.listing_species}</span>
        <h3>{order.listing_title}</h3>
        <p>{order.listing_location}</p>
      </div>
      <div className="mb-order-values">
        <strong>{number(order.quantity_kg, ' kg')}</strong>
        <span>{money(order.total_price)}</span>
        <StatusBadge status={order.status} />
      </div>
      <div className="mb-order-people">
        <span>Buyer: {order.buyer_name}</span>
        <span>Seller: {order.seller_name}</span>
      </div>
      <div className="mb-order-actions">
        {isSeller && order.status === 'pending' && (
          <>
            <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('accept', order.id)}>Accept</button>
            <button type="button" className="mb-btn mb-btn-secondary" onClick={() => onAction('reject', order.id)}>Reject</button>
          </>
        )}
        {isSeller && order.status === 'accepted' && (
          <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('complete', order.id)}>Complete</button>
        )}
        {isBuyer && order.status === 'pending' && (
          <button type="button" className="mb-btn mb-btn-secondary" onClick={() => onAction('cancel', order.id)}>Cancel</button>
        )}
      </div>
    </article>
  );
}

export default function MarketBridge() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('store');
  const [profile, setProfile] = useState(null);
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [orders, setOrders] = useState([]);
  const [ponds, setPonds] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [form, setForm] = useState(EMPTY_FORM);
  const [orderDraft, setOrderDraft] = useState({ listing: null, quantity_kg: '', buyer_note: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const canSell = profile?.can_sell ?? user?.market_profile?.can_sell ?? true;
  const canBuy = profile?.can_buy ?? user?.market_profile?.can_buy ?? true;

  const summary = useMemo(() => {
    const activeListings = listings.filter(item => item.status === 'active');
    const availableKg = activeListings.reduce((total, item) => total + Number(item.available_quantity_kg || 0), 0);
    const pendingOrders = orders.filter(order => order.status === 'pending').length;
    return { activeListings: activeListings.length, availableKg, pendingOrders };
  }, [listings, orders]);

  useEffect(() => {
    let mounted = true;

    async function loadInitial() {
      setLoading(true);
      setError('');
      try {
        const [profileData, listingData, myListingData, orderData, pondData] = await Promise.all([
          getMarketProfile(),
          getMarketListings(),
          getMarketListings({ mine: true }),
          getMarketOrders(),
          getPonds(),
        ]);
        if (!mounted) return;
        setProfile(profileData);
        setListings(listingData || []);
        setMyListings(myListingData || []);
        setOrders(orderData || []);
        setPonds(pondData || []);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadInitial();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedPondId) {
      setStocks([]);
      return;
    }

    let mounted = true;
    getPondStocks(selectedPondId)
      .then(data => {
        if (mounted) setStocks(data || []);
      })
      .catch(() => {
        if (mounted) setStocks([]);
      });

    return () => {
      mounted = false;
    };
  }, [selectedPondId]);

  async function reloadMarket() {
    const [listingData, myListingData, orderData] = await Promise.all([
      getMarketListings(),
      getMarketListings({ mine: true }),
      getMarketOrders(),
    ]);
    setListings(listingData || []);
    setMyListings(myListingData || []);
    setOrders(orderData || []);
  }

  function updateForm(event) {
    const { name, value, files } = event.target;
    const nextValue = files ? files[0] : value;
    setForm(current => ({ ...current, [name]: nextValue }));

    if (name === 'fish_stock') {
      const stock = stocks.find(item => String(item.id) === value);
      if (stock) {
        setForm(current => ({
          ...current,
          fish_stock: value,
          species: stock.species,
          title: `${stock.species} from ${stock.batch_name}`,
        }));
      }
    }
  }

  async function updateRole(event) {
    const nextRole = event.target.value;
    setProfile(current => ({ ...current, role: nextRole }));
    try {
      const data = await updateMarketProfile({ role: nextRole });
      setProfile(data);
      setMessage('Market role updated.');
    } catch (err) {
      setError(err.message);
    }
  }

  async function suggestPrice() {
    setError('');
    try {
      const data = await getMarketPriceRecommendation({
        species: form.species,
        location: form.location,
        quantity_kg: form.quantity_kg,
        fish_stock: form.fish_stock || undefined,
      });
      setForm(current => ({
        ...current,
        suggested_price: data.suggested_price,
        unit_price: current.unit_price || data.suggested_price,
      }));
      setMessage(`Suggested range: ${money(data.low_price)} to ${money(data.high_price)} per kg.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitListing(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');

    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        payload.append(key, value);
      }
    });

    try {
      await createMarketListing(payload);
      setForm(EMPTY_FORM);
      setSelectedPondId('');
      await reloadMarket();
      setActiveTab('store');
      setMessage('Listing created.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function submitOrder(event) {
    event.preventDefault();
    if (!orderDraft.listing) return;

    setSaving(true);
    setError('');
    setMessage('');
    try {
      await createMarketOrder({
        listing: orderDraft.listing.id,
        quantity_kg: orderDraft.quantity_kg,
        buyer_note: orderDraft.buyer_note,
      });
      setOrderDraft({ listing: null, quantity_kg: '', buyer_note: '' });
      await reloadMarket();
      setActiveTab('orders');
      setMessage('Order request sent.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleOrderAction(action, id) {
    const actions = {
      accept: acceptMarketOrder,
      reject: rejectMarketOrder,
      complete: completeMarketOrder,
      cancel: cancelMarketOrder,
    };

    setSaving(true);
    setError('');
    setMessage('');
    try {
      await actions[action](id);
      await reloadMarket();
      setMessage('Order updated.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="mb-root" aria-labelledby="market-bridge-title">
      <div className="mb-header">
        <div>
          <span>Market Bridge</span>
          <h1 id="market-bridge-title">Fish Store</h1>
        </div>
        <label className="mb-role">
          <span>Role</span>
          <select value={profile?.role || 'both'} onChange={updateRole}>
            <option value="both">Buyer and seller</option>
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
          </select>
        </label>
      </div>

      <div className="mb-summary">
        <article>
          <span>Active Listings</span>
          <strong>{summary.activeListings}</strong>
        </article>
        <article>
          <span>Available Fish</span>
          <strong>{number(summary.availableKg, ' kg')}</strong>
        </article>
        <article>
          <span>Pending Orders</span>
          <strong>{summary.pendingOrders}</strong>
        </article>
      </div>

      <div className="mb-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            type="button"
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {message && <StatePanel type="success">{message}</StatePanel>}
      {error && <StatePanel type="error">{error}</StatePanel>}

      {loading ? (
        <StatePanel>Loading market bridge...</StatePanel>
      ) : activeTab === 'store' ? (
        <div className="mb-grid">
          {listings.length ? listings.map(listing => (
            <ListingCard
              key={listing.id}
              listing={listing}
              currentUserId={user?.id}
              onOrder={listing => setOrderDraft({ listing, quantity_kg: '', buyer_note: '' })}
            />
          )) : (
            <StatePanel>No active fish listings found.</StatePanel>
          )}
        </div>
      ) : activeTab === 'sell' ? (
        <div className="mb-sell-layout">
          <form className="mb-panel mb-form" onSubmit={submitListing}>
            <div className="mb-panel-title">
              <span>New Listing</span>
              <h2>Stock fish for sale</h2>
            </div>

            {!canSell && <StatePanel type="error">Your account is not approved for seller actions.</StatePanel>}

            <div className="mb-grid-two">
              <label className="mb-field">
                <span>Source</span>
                <select name="source_type" value={form.source_type} onChange={updateForm}>
                  <option value="manual">Manual stock</option>
                  <option value="inventory">From inventory</option>
                </select>
              </label>

              {form.source_type === 'inventory' && (
                <label className="mb-field">
                  <span>Pond</span>
                  <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
                    <option value="">Select pond</option>
                    {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
                  </select>
                </label>
              )}
            </div>

            {form.source_type === 'inventory' && (
              <label className="mb-field">
                <span>Fish stock</span>
                <select name="fish_stock" value={form.fish_stock} onChange={updateForm} required>
                  <option value="">Select stock</option>
                  {stocks.map(stock => (
                    <option key={stock.id} value={stock.id}>
                      {stock.batch_name} - {stock.species} ({number(stock.current_quantity)} fish)
                    </option>
                  ))}
                </select>
              </label>
            )}

            <div className="mb-grid-two">
              <label className="mb-field">
                <span>Species</span>
                <input name="species" value={form.species} onChange={updateForm} required />
              </label>
              <label className="mb-field">
                <span>Title</span>
                <input name="title" value={form.title} onChange={updateForm} required />
              </label>
            </div>

            <div className="mb-grid-three">
              <label className="mb-field">
                <span>Quantity kg</span>
                <input type="number" min="0.01" step="0.01" name="quantity_kg" value={form.quantity_kg} onChange={updateForm} required />
              </label>
              <label className="mb-field">
                <span>Price per kg</span>
                <input type="number" min="0.01" step="0.01" name="unit_price" value={form.unit_price} onChange={updateForm} required />
              </label>
              <label className="mb-field">
                <span>Suggested</span>
                <input value={form.suggested_price ? money(form.suggested_price) : ''} readOnly />
              </label>
            </div>

            <div className="mb-form-actions">
              <button type="button" className="mb-btn mb-btn-secondary" onClick={suggestPrice}>
                Suggest price
              </button>
            </div>

            <div className="mb-grid-two">
              <label className="mb-field">
                <span>Location</span>
                <input name="location" value={form.location} onChange={updateForm} required />
              </label>
              <label className="mb-field">
                <span>Available from</span>
                <input type="date" name="available_from" value={form.available_from} onChange={updateForm} />
              </label>
            </div>

            <label className="mb-field">
              <span>Picture</span>
              <input type="file" name="photo" accept="image/*" onChange={updateForm} />
            </label>

            <label className="mb-field">
              <span>Description</span>
              <textarea name="description" rows="3" value={form.description} onChange={updateForm} />
            </label>

            <button type="submit" className="mb-btn mb-btn-primary" disabled={saving || !canSell}>
              {saving ? 'Saving...' : 'Create listing'}
            </button>
          </form>

          <section className="mb-panel">
            <div className="mb-panel-title">
              <span>My Listings</span>
              <h2>Seller store</h2>
            </div>
            <div className="mb-mini-list">
              {myListings.length ? myListings.map(listing => (
                <article key={listing.id}>
                  <div>
                    <strong>{listing.title}</strong>
                    <span>{number(listing.available_quantity_kg, ' kg')} at {money(listing.unit_price)}</span>
                  </div>
                  <StatusBadge status={listing.status} />
                </article>
              )) : (
                <StatePanel>No seller listings yet.</StatePanel>
              )}
            </div>
          </section>
        </div>
      ) : (
        <div className="mb-orders">
          {orders.length ? orders.map(order => (
            <OrderRow
              key={order.id}
              order={order}
              currentUserId={user?.id}
              onAction={handleOrderAction}
            />
          )) : (
            <StatePanel>No market orders yet.</StatePanel>
          )}
        </div>
      )}

      {orderDraft.listing && (
        <div className="mb-modal-backdrop" role="presentation">
          <form className="mb-modal" onSubmit={submitOrder}>
            <div className="mb-panel-title">
              <span>Order Request</span>
              <h2>{orderDraft.listing.title}</h2>
            </div>
            {!canBuy && <StatePanel type="error">Your account is not approved for buyer actions.</StatePanel>}
            <label className="mb-field">
              <span>Quantity kg</span>
              <input
                type="number"
                min="0.01"
                max={orderDraft.listing.available_quantity_kg}
                step="0.01"
                value={orderDraft.quantity_kg}
                onChange={event => setOrderDraft(current => ({ ...current, quantity_kg: event.target.value }))}
                required
              />
            </label>
            <label className="mb-field">
              <span>Note</span>
              <textarea
                rows="3"
                value={orderDraft.buyer_note}
                onChange={event => setOrderDraft(current => ({ ...current, buyer_note: event.target.value }))}
              />
            </label>
            <div className="mb-modal-actions">
              <button type="button" className="mb-btn mb-btn-secondary" onClick={() => setOrderDraft({ listing: null, quantity_kg: '', buyer_note: '' })}>
                Close
              </button>
              <button type="submit" className="mb-btn mb-btn-primary" disabled={saving || !canBuy}>
                Send request
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
