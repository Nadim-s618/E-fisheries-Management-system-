import React, { useEffect, useMemo, useState } from 'react';

import {
  acceptMarketOrder,
  completeMarketOrder,
  createMarketListing,
  deliverMarketOrder,
  getMarketListings,
  getMarketOrders,
  getMarketPriceRecommendation,
  getMarketProfile,
  getPondStocks,
  updateMarketListing,
  getPonds,
  rejectMarketOrder,
  shipMarketOrder,
} from '../../lib/api';
import { useAuth } from '../../context/useAuth';
import './MarketBridge.css';

const TABS = [
  { id: 'sell', label: 'Sell' },
  { id: 'orders', label: 'Orders' },
];

const EMPTY_FORM = {
  source_type: 'manual',
  fish_stock: '',
  species: '',
  average_height_cm: '',
  average_weight_g: '',
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

function StatusBadge({ status }) {
  return <span className={`mb-badge mb-badge-${status}`}>{status.replaceAll('_', ' ')}</span>;
}

function StatePanel({ type = 'empty', children }) {
  return <div className={`mb-state mb-state-${type}`}>{children}</div>;
}

function OrderRow({ order, currentUserId, onAction }) {
  const isSeller = order.seller === currentUserId;
  const [showBuyerDetails, setShowBuyerDetails] = useState(false);

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
        <button type="button" className="mb-btn mb-btn-secondary" onClick={() => setShowBuyerDetails(current => !current)}>
          {showBuyerDetails ? 'Hide buyer details' : 'View buyer details'}
        </button>
        {isSeller && order.status === 'pending' && (
          <>
            <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('accept', order.id)}>Accept</button>
            <button type="button" className="mb-btn mb-btn-secondary" onClick={() => onAction('reject', order.id)}>Reject</button>
          </>
        )}
        {isSeller && order.status === 'accepted' && (
          <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('ship', order.id)}>Mark shipped</button>
        )}
        {isSeller && order.status === 'shipped' && (
          <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('deliver', order.id)}>Send for delivery</button>
        )}
        {isSeller && order.status === 'out_for_delivery' && (
          <button type="button" className="mb-btn mb-btn-primary" onClick={() => onAction('complete', order.id)}>Complete</button>
        )}
      </div>
      {showBuyerDetails && (
        <div className="mb-buyer-details">
          <div className="mb-buyer-details-header">
            <strong>Buyer details</strong>
            <StatusBadge status={order.status} />
          </div>
          <dl>
            <div><dt>Account</dt><dd>{order.buyer_name}{order.buyer_username ? ` · @${order.buyer_username}` : ' · Guest buyer'}</dd></div>
            {order.buyer_email && <div><dt>Email</dt><dd>{order.buyer_email}</dd></div>}
            <div><dt>Full name</dt><dd>{order.buyer_full_name || '--'}</dd></div>
            <div><dt>Phone</dt><dd>{order.buyer_contact_number || '--'}</dd></div>
            <div><dt>Address</dt><dd>{order.buyer_address || '--'}</dd></div>
            <div><dt>Buyer note</dt><dd>{order.buyer_note || 'No note'}</dd></div>
            <div><dt>Order</dt><dd>{number(order.quantity_kg, ' kg')} · {money(order.unit_price)}/kg · {money(order.total_price)}</dd></div>
            <div><dt>Transaction</dt><dd>{order.transaction_code || '--'}</dd></div>
          </dl>
        </div>
      )}
    </article>
  );
}

export default function MarketBridge() {
  const { user } = useAuth();
  const currentUserId = user?.id;
  const [activeTab, setActiveTab] = useState('sell');
  const [profile, setProfile] = useState(null);
  const [myListings, setMyListings] = useState([]);
  const [orders, setOrders] = useState([]);
  const [ponds, setPonds] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [editingListingId, setEditingListingId] = useState(null);
  const [listingEditForm, setListingEditForm] = useState(null);
  const [listingView, setListingView] = useState('current');

  const canSell = profile?.can_sell ?? user?.market_profile?.can_sell ?? true;

  const summary = useMemo(() => {
    const activeListings = myListings.filter(item => (
      item.status === 'active' && Number(item.available_quantity_kg || 0) > 0
    ));
    const availableKg = activeListings.reduce((total, item) => total + Number(item.available_quantity_kg || 0), 0);
    const pendingOrders = orders.filter(order => order.status === 'pending').length;
    return { activeListings: activeListings.length, availableKg, pendingOrders };
  }, [myListings, orders]);

  useEffect(() => {
    let mounted = true;

    async function loadInitial() {
      setLoading(true);
      setError('');
      try {
        const [profileData, myListingData, orderData, pondData] = await Promise.all([
          getMarketProfile(),
          getMarketListings({ mine: true }),
          getMarketOrders(),
          getPonds(),
        ]);
        if (!mounted) return;
        setProfile(profileData);
        setMyListings(myListingData || []);
        setOrders((orderData || []).filter(order => String(order.seller) === String(currentUserId)));
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
  }, [currentUserId]);

  useEffect(() => {
    if (!selectedPondId) {
      queueMicrotask(() => {
        setStocks([]);
      });
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
    const [myListingData, orderData] = await Promise.all([
      getMarketListings({ mine: true }),
      getMarketOrders(),
    ]);
    setMyListings(myListingData || []);
    setOrders((orderData || []).filter(order => String(order.seller) === String(currentUserId)));
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

  async function handleOrderAction(action, id) {
    const actions = {
      accept: acceptMarketOrder,
      reject: rejectMarketOrder,
      ship: shipMarketOrder,
      deliver: deliverMarketOrder,
      complete: completeMarketOrder,
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

  function startListingEdit(listing, relist = false) {
    setEditingListingId(listing.id);
    setListingEditForm({
      quantity_kg: listing.quantity_kg,
      available_quantity_kg: relist ? listing.quantity_kg : listing.available_quantity_kg,
      unit_price: listing.unit_price,
      status: relist || listing.status === 'sold_out' ? 'active' : listing.status,
      description: listing.description || '',
    });
    setError('');
  }

  async function saveListingEdit(event, listingId) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await updateMarketListing(listingId, {
        ...listingEditForm,
        quantity_kg: Number(listingEditForm.quantity_kg),
        available_quantity_kg: Number(listingEditForm.available_quantity_kg),
        unit_price: Number(listingEditForm.unit_price),
      });
      setEditingListingId(null);
      setListingEditForm(null);
      await reloadMarket();
      setMessage('Listing updated.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function closeListing(listingId) {
    setSaving(true);
    setError('');
    try {
      await updateMarketListing(listingId, { status: 'closed' });
      setEditingListingId(null);
      setListingEditForm(null);
      await reloadMarket();
      setMessage('Listing closed.');
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

            <div className="mb-grid-two">
              <label className="mb-field">
                <span>Average height (cm)</span>
                <input type="number" min="0.01" step="0.01" name="average_height_cm" value={form.average_height_cm} onChange={updateForm} required />
              </label>
              <label className="mb-field">
                <span>Average weight (g)</span>
                <input type="number" min="0.01" step="0.01" name="average_weight_g" value={form.average_weight_g} onChange={updateForm} required />
              </label>
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
            <div className="mb-listing-view-toggle" role="tablist" aria-label="Listing views">
              <button type="button" className={listingView === 'current' ? 'active' : ''} onClick={() => setListingView('current')}>Current listings</button>
              <button type="button" className={listingView === 'history' ? 'active' : ''} onClick={() => setListingView('history')}>Listing history</button>
            </div>
            <div className="mb-mini-list">
              {myListings.filter(listing => listingView === 'history' ? ['closed', 'sold_out'].includes(listing.status) : !['closed', 'sold_out'].includes(listing.status)).length ? myListings.filter(listing => listingView === 'history' ? ['closed', 'sold_out'].includes(listing.status) : !['closed', 'sold_out'].includes(listing.status)).map(listing => (
                <article key={listing.id}>
                  <div className="mb-listing-summary">
                    <strong>{listing.title}</strong>
                    <span>{number(listing.available_quantity_kg, ' kg')} at {money(listing.unit_price)}</span>
                  </div>
                  <StatusBadge status={listing.status} />
                  <div className="mb-listing-controls">
                    {listingView === 'history' ? (
                      <button type="button" className="mb-btn mb-btn-primary" onClick={() => startListingEdit(listing, true)}>Relist</button>
                    ) : (
                      <>
                        <button type="button" className="mb-btn mb-btn-secondary" onClick={() => startListingEdit(listing)}>Edit</button>
                        {listing.status !== 'closed' && <button type="button" className="mb-btn mb-btn-danger" onClick={() => closeListing(listing.id)} disabled={saving}>Close</button>}
                      </>
                    )}
                  </div>
                  {editingListingId === listing.id && listingEditForm && (
                    <form className="mb-listing-edit" onSubmit={event => saveListingEdit(event, listing.id)}>
                      <div className="mb-grid-two">
                        <label className="mb-field"><span>Listed stock (kg)</span><input type="number" min="0.01" step="0.01" value={listingEditForm.quantity_kg} onChange={event => setListingEditForm(current => ({ ...current, quantity_kg: event.target.value }))} required /></label>
                        <label className="mb-field"><span>Available stock (kg)</span><input type="number" min="0" step="0.01" value={listingEditForm.available_quantity_kg} onChange={event => setListingEditForm(current => ({ ...current, available_quantity_kg: event.target.value }))} required /></label>
                        <label className="mb-field"><span>Price per kg</span><input type="number" min="0.01" step="0.01" value={listingEditForm.unit_price} onChange={event => setListingEditForm(current => ({ ...current, unit_price: event.target.value }))} required /></label>
                        <label className="mb-field"><span>Status</span><select value={listingEditForm.status} onChange={event => setListingEditForm(current => ({ ...current, status: event.target.value }))}><option value="active">Active</option><option value="paused">Paused</option><option value="closed">Closed</option></select></label>
                      </div>
                      <label className="mb-field"><span>Description</span><textarea rows="2" value={listingEditForm.description} onChange={event => setListingEditForm(current => ({ ...current, description: event.target.value }))} /></label>
                      <div className="mb-modal-actions"><button type="button" className="mb-btn mb-btn-secondary" onClick={() => setEditingListingId(null)}>Cancel</button><button type="submit" className="mb-btn mb-btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save changes'}</button></div>
                    </form>
                  )}
                </article>
              )) : (
                <StatePanel>{listingView === 'history' ? 'No closed or sold-out listings yet.' : 'No current listings yet.'}</StatePanel>
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
              currentUserId={currentUserId}
              onAction={handleOrderAction}
            />
          )) : (
            <StatePanel>No market orders yet.</StatePanel>
          )}
        </div>
      )}

    </section>
  );
}
