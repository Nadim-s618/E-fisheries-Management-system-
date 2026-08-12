import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { createPublicMashrafeeCartOrder, getPublicMashrafeeStore, trackPublicMashrafeeOrder } from '../lib/api';
import './HomePage.css';
import './FishStore.css';

const emptyOrderForm = {
  quantity_kg: '',
  buyer_full_name: '',
  buyer_address: '',
  buyer_contact_number: '',
  buyer_note: '',
};

function receiptMoney(value) {
  return `BDT ${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function receiptNumber(value) {
  return `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })} kg`;
}

const trackingSteps = [
  { status: 'pending', label: 'Order placed' },
  { status: 'accepted', label: 'Accepted' },
  { status: 'shipped', label: 'Shipped' },
  { status: 'out_for_delivery', label: 'Out for delivery' },
  { status: 'completed', label: 'Completed' },
];

function OrderRoute({ order }) {
  const terminalStatus = order.status === 'cancelled' || order.status === 'rejected';
  const foundIndex = trackingSteps.findIndex(step => step.status === order.status);
  const currentIndex = foundIndex >= 0 ? foundIndex : 0;

  return (
    <div className="fs-order-route" aria-label={`Order route: ${order.status_display}`}>
      <div className="fs-order-route-header">
        <strong>{order.listing_title}</strong>
        <span>{order.listing_species || 'Fish'} · {order.status_display}</span>
      </div>
      {terminalStatus ? (
        <div className="fs-route-terminal">
          <span className="fs-route-dot" aria-hidden="true">!</span>
          <span>This order was {order.status_display.toLowerCase()}.</span>
        </div>
      ) : (
        <ol className="fs-route-steps">
          {trackingSteps.map((step, index) => (
            <li
              key={step.status}
              className={index < currentIndex ? 'is-complete' : index === currentIndex ? 'is-current' : ''}
            >
              <span className="fs-route-dot" aria-hidden="true">{index < currentIndex ? '✓' : index + 1}</span>
              <span>{step.label}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function Receipt({ receipt }) {
  const total = receipt.orders.reduce((sum, order) => sum + Number(order.total_price || 0), 0);
  const firstOrder = receipt.orders[0] || {};

  return (
    <section className="fs-receipt" aria-labelledby="receipt-title">
      <div className="fs-receipt-header">
        <div><span className="fs-eyebrow fs-eyebrow-small">Order receipt</span><h2 id="receipt-title">Fish Store Receipt</h2></div>
        <button type="button" className="fs-receipt-print" onClick={() => window.print()}>Print receipt</button>
      </div>
      <div className="fs-receipt-code"><span>Tracking code</span><strong>{receipt.transaction_code}</strong></div>
      <div className="fs-receipt-buyer">
        <div><span>Buyer</span><strong>{receipt.buyer_full_name}</strong></div>
        <div><span>Phone</span><strong>{receipt.buyer_contact_number}</strong></div>
        <div><span>Address</span><strong>{receipt.buyer_address}</strong></div>
        {receipt.buyer_note && <div><span>Note</span><strong>{receipt.buyer_note}</strong></div>}
      </div>
      <div className="fs-receipt-items">
        {receipt.orders.map(order => (
          <div className="fs-receipt-item" key={`${order.id || order.transaction_code}-${order.listing_title}`}>
            <div><strong>{order.listing_title}</strong><span>{order.listing_species || 'Fish'} · {order.status_display || 'Pending'}</span></div>
            <div><span>{receiptNumber(order.quantity_kg)} × {receiptMoney(order.unit_price)}</span><strong>{receiptMoney(order.total_price)}</strong></div>
          </div>
        ))}
      </div>
      <div className="fs-receipt-total"><span>Total</span><strong>{receiptMoney(total)}</strong></div>
      <p className="fs-receipt-footnote">Use the tracking code to check your order status. Keep this receipt for your records.</p>
      {firstOrder.created_at && <small className="fs-receipt-date">Ordered {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(firstOrder.created_at))}</small>}
    </section>
  );
}

export default function FishStorePage() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [quantityListing, setQuantityListing] = useState(null);
  const [quantityValue, setQuantityValue] = useState('1');
  const [orderForm, setOrderForm] = useState(emptyOrderForm);
  const [orderSaving, setOrderSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [trackingCode, setTrackingCode] = useState('');
  const [trackingResult, setTrackingResult] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getPublicMashrafeeStore()
      .then(data => {
        if (isMounted) {
          setListings(data || []);
          setError('');
        }
      })
      .catch(() => {
        if (isMounted) setError('The fish store is unavailable right now.');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  function updateOrderForm(event) {
    const { name, value } = event.target;
    setOrderForm(current => ({ ...current, [name]: value }));
  }

  function addToCart(listing, quantity = 1) {
    setCart(current => {
      const existing = current.find(item => item.id === listing.id);
      if (existing) {
        return current.map(item => item.id === listing.id
          ? { ...item, quantity_kg: Math.min(Number(item.quantity_kg) + Number(quantity), Number(listing.available_quantity_kg)) }
          : item);
      }
      return [...current, { ...listing, quantity_kg: Math.min(Number(quantity), Number(listing.available_quantity_kg)) }];
    });
    setMessage(`${listing.title} added to your cart.`);
    setError('');
  }

  function openQuantitySelector(listing) {
    setQuantityListing(listing);
    setQuantityValue('1');
    setMessage('');
  }

  function submitQuantity(event) {
    event.preventDefault();
    if (!quantityListing) return;
    addToCart(quantityListing, quantityValue);
    setQuantityListing(null);
  }

  function updateCartQuantity(listingId, quantity) {
    setCart(current => current.map(item => item.id === listingId
      ? { ...item, quantity_kg: quantity }
      : item));
  }

  function removeFromCart(listingId) {
    setCart(current => current.filter(item => item.id !== listingId));
  }

  const cartCount = cart.length;
  const cartTotal = cart.reduce((total, item) => total + (Number(item.quantity_kg) * Number(item.unit_price)), 0);
  const normalizedSearch = searchQuery.trim().toLowerCase();
  const filteredListings = listings.filter(listing => (
    !normalizedSearch
    || listing.title.toLowerCase().includes(normalizedSearch)
    || listing.species.toLowerCase().includes(normalizedSearch)
  ));

  async function submitCartOrder(event) {
    event.preventDefault();
    if (!cart.length) return;

    setOrderSaving(true);
    setMessage('');
    setError('');

    try {
      const createdOrders = await createPublicMashrafeeCartOrder({
        items: cart.map(item => ({ listing: item.id, quantity_kg: item.quantity_kg })),
        buyer_full_name: orderForm.buyer_full_name,
        buyer_address: orderForm.buyer_address,
        buyer_contact_number: orderForm.buyer_contact_number,
        buyer_note: orderForm.buyer_note,
      });
      const receiptBuyer = { ...orderForm };
      setCart([]);
      setCartOpen(false);
      setOrderForm(emptyOrderForm);
      const transactionCode = createdOrders?.[0]?.transaction_code;
      setTrackingCode(transactionCode || '');
      setTrackingResult(transactionCode ? { transaction_code: transactionCode, orders: createdOrders } : null);
      setReceipt(transactionCode ? { transaction_code: transactionCode, orders: createdOrders, ...receiptBuyer } : null);
      setMessage(transactionCode
        ? `Order placed. Your transaction code is ${transactionCode}.`
        : 'Your cart order has been sent to Mashrafee.');
    } catch (orderError) {
      setError(orderError.message || 'Unable to place the order.');
    } finally {
      setOrderSaving(false);
    }
  }

  async function trackOrder(event) {
    event.preventDefault();
    if (!trackingCode.trim()) return;
    setTrackingLoading(true);
    setError('');
    try {
      const result = await trackPublicMashrafeeOrder(trackingCode.trim());
      setTrackingResult(result);
    } catch (trackError) {
      setTrackingResult(null);
      setError(trackError.message || 'Transaction code not found.');
    } finally {
      setTrackingLoading(false);
    }
  }

  return (
    <div className="homepage fish-store-page">
      <nav className="navbar fs-navbar">
        <div className="navbar-inner">
          <Link to="/" className="logo">
            <img src="/logo.png" alt="E-Fisheries logo" className="logo-icon" />
            <span className="logo-text">
              <span className="logo-name">E-Fisheries</span>
              <span className="logo-sub">Management System</span>
            </span>
          </Link>
          <div className="nav-auth">
            <Link to="/" className="btn-nav">Back to home</Link>
            <Link to="/login" className="btn-nav">Sign in</Link>
          </div>
        </div>
      </nav>

      <header className="fs-hero">
        <div className="fs-hero-tools">
          {searchOpen && (
            <label className="fs-search-box">
              <span className="sr-only">Search fish</span>
              <input
                type="search"
                placeholder="Search fish..."
                value={searchQuery}
                onChange={event => setSearchQuery(event.target.value)}
                autoFocus
              />
            </label>
          )}
          <button type="button" className="fs-search-button" onClick={() => setSearchOpen(current => !current)} aria-label="Search fish" aria-expanded={searchOpen}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.3" /><path d="m16 16 4.5 4.5" /></svg>
          </button>
          <button type="button" className="fs-cart-button fs-hero-cart" onClick={() => setCartOpen(true)} aria-label={`Open cart with ${cartCount} item${cartCount === 1 ? '' : 's'}`}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h7.9a2 2 0 0 0 1.9-1.5L20.5 7H6.1M10 20a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm9 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z" /></svg>
            {cartCount > 0 && <span className="fs-cart-count">{cartCount}</span>}
          </button>
        </div>
        <div className="fs-hero-inner">
          <Link to="/" className="store-back-link">← Back to homepage</Link>
          <p className="fs-eyebrow">Direct from Mashrafee</p>
          <h1 className="fs-title">Fish Store<span className="fs-title-of"> of </span>Mashrafee</h1>
          <p className="fs-sub">Order fresh fish straight from Mashrafee's counter. No account needed.</p>
        </div>
        <svg className="fs-wave" viewBox="0 0 1200 60" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,32 C150,60 350,0 600,28 C850,56 1050,4 1200,30 L1200,60 L0,60 Z" />
        </svg>
      </header>

      <main className="homepage-store store-page-main fs-main">
        <div className="section-inner">
          {message && <div className="fs-banner fs-banner-success" role="status">{message}</div>}
          {error && <div className="fs-banner fs-banner-error" role="alert">{error}</div>}

          <section className="fs-tracking-panel" aria-labelledby="track-order-title">
            <div>
              <span className="fs-eyebrow fs-eyebrow-small">Order lookup</span>
              <h2 id="track-order-title">Track your order</h2>
              <p>Enter the transaction code you received after ordering.</p>
            </div>
            <form className="fs-tracking-form" onSubmit={trackOrder}>
              <input
                type="text"
                placeholder="Example: MF-A1B2C3D4"
                value={trackingCode}
                onChange={event => setTrackingCode(event.target.value.toUpperCase())}
                aria-label="Transaction code"
              />
              <button type="submit" className="fs-submit-button" disabled={trackingLoading}>
                {trackingLoading ? 'Checking…' : 'Track'}
              </button>
            </form>
            {trackingResult && (
              <div className="fs-tracking-result" role="status">
                <strong>{trackingResult.transaction_code}</strong>
                <div className="fs-tracking-orders">
                  {trackingResult.orders.map(order => (
                    <OrderRoute key={`${order.transaction_code}-${order.listing_title}`} order={order} />
                  ))}
                </div>
              </div>
            )}
          </section>

          {receipt && <Receipt receipt={receipt} />}

          {loading ? (
            <div className="fs-state">
              <span className="fs-state-icon" aria-hidden="true">🐟</span>
              Bringing in today's catch…
            </div>
          ) : filteredListings.length ? (
            <div className="fs-grid">
              {filteredListings.map(listing => (
                <article className="fs-card" key={listing.id}>
                  <div className="fs-tag" style={{ '--fs-tag-tilt': `${(listing.id % 5) - 2}deg` }}>
                    <span className="fs-tag-hole" aria-hidden="true" />
                    <span className="fs-tag-price">{Number(listing.unit_price).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    <span className="fs-tag-unit">BDT/kg</span>
                  </div>

                  <div className="fs-card-image">
                    {listing.photo_url ? (
                      <img src={listing.photo_url} alt={listing.title} />
                    ) : (
                      <span className="fs-card-initials">{listing.species?.slice(0, 2).toUpperCase() || 'FS'}</span>
                    )}
                  </div>

                  <div className="fs-card-body">
                    <span className="fs-species">{listing.species}</span>
                    <h2 className="fs-card-title">{listing.title}</h2>
                    <p className="fs-location">{listing.location}</p>
                    <div className="fs-stock-line">
                      <span className="fs-stock-dot" aria-hidden="true" />
                      {Number(listing.available_quantity_kg).toLocaleString()} kg on ice
                    </div>
                    <div className="fs-measurements">
                      <span>Avg height: {listing.average_height_cm ? `${Number(listing.average_height_cm).toLocaleString()} cm` : '--'}</span>
                      <span>Avg weight: {listing.average_weight_g ? `${Number(listing.average_weight_g).toLocaleString()} g` : '--'}</span>
                    </div>
                    <div className="fs-card-actions">
                      <button type="button" className="fs-cart-add-button" onClick={() => openQuantitySelector(listing)}>
                        <svg className="fs-add-cart-icon" viewBox="0 0 32 32" aria-hidden="true">
                          <path d="M4 6h3l2.2 13.2a2 2 0 0 0 2 1.7h10.6a2 2 0 0 0 1.9-1.5L26 10H8.1" />
                          <circle cx="12" cy="26" r="1.6" />
                          <circle cx="23" cy="26" r="1.6" />
                          <path d="M24 3v6M21 6h6" />
                        </svg>
                        Add to cart
                      </button>
                      <button type="button" className="fs-order-button" onClick={() => { addToCart(listing); setCartOpen(true); }}>
                        Place order
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="fs-state fs-state-empty">
              <span className="fs-state-icon" aria-hidden="true">🌊</span>
              {normalizedSearch ? `No fish found for “${searchQuery}”.` : "The catch hasn't come in yet. Check back soon."}
            </div>
          )}
        </div>
      </main>

      {quantityListing && (
        <div className="fs-modal-backdrop" role="presentation">
          <form className="fs-slip fs-quantity-slip" onSubmit={submitQuantity}>
            <div className="fs-slip-perforation" aria-hidden="true" />
            <div className="fs-slip-header">
              <div>
                <span className="fs-eyebrow fs-eyebrow-small">Add to cart</span>
                <h2>{quantityListing.title}</h2>
              </div>
              <button type="button" className="fs-slip-close" onClick={() => setQuantityListing(null)} aria-label="Close quantity form">×</button>
            </div>
            <p className="fs-slip-price">
              <span className="fs-slip-price-value">BDT {Number(quantityListing.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              <span className="fs-slip-price-unit">/kg</span>
              <span className="fs-slip-price-stock">{Number(quantityListing.available_quantity_kg).toLocaleString()} kg available</span>
            </p>
            <label className="fs-field">
              <span>How many kilograms?</span>
              <input
                type="number"
                min="0.01"
                max={quantityListing.available_quantity_kg}
                step="0.01"
                value={quantityValue}
                onChange={event => setQuantityValue(event.target.value)}
                required
                autoFocus
              />
            </label>
            <div className="fs-slip-actions">
              <button type="button" className="fs-cancel-button" onClick={() => setQuantityListing(null)}>Cancel</button>
              <button type="submit" className="fs-submit-button">Add to cart</button>
            </div>
          </form>
        </div>
      )}

      {cartOpen && (
        <div className="fs-modal-backdrop" role="presentation">
          <form className="fs-slip fs-cart-slip" onSubmit={submitCartOrder}>
            <div className="fs-slip-perforation" aria-hidden="true" />
            <div className="fs-slip-header">
              <div>
                <span className="fs-eyebrow fs-eyebrow-small">Your selection</span>
                <h2>Fish cart</h2>
              </div>
              <button
                type="button"
                className="fs-slip-close"
                onClick={() => setCartOpen(false)}
                aria-label="Close cart"
              >
                ×
              </button>
            </div>

            {cart.length ? (
              <>
                <div className="fs-cart-items">
                  {cart.map(item => (
                    <div className="fs-cart-item" key={item.id}>
                      <div className="fs-cart-item-info">
                        <strong>{item.title}</strong>
                        <span>BDT {Number(item.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}/kg</span>
                      </div>
                      <input
                        className="fs-cart-quantity"
                        aria-label={`Quantity of ${item.title} in kilograms`}
                        type="number"
                        min="0.01"
                        max={item.available_quantity_kg}
                        step="0.01"
                        value={item.quantity_kg}
                        onChange={event => updateCartQuantity(item.id, event.target.value)}
                      />
                      <button type="button" className="fs-cart-remove" onClick={() => removeFromCart(item.id)} aria-label={`Remove ${item.title} from cart`}>×</button>
                    </div>
                  ))}
                </div>
                <div className="fs-cart-total">
                  <span>Estimated total</span>
                  <strong>BDT {cartTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                </div>

                <p className="fs-cart-checkout-label">Delivery details</p>
            <label className="fs-field">
              <span>Your name</span>
              <input name="buyer_full_name" value={orderForm.buyer_full_name} onChange={updateOrderForm} required />
            </label>
            <label className="fs-field">
              <span>Mobile number</span>
              <input name="buyer_contact_number" type="tel" value={orderForm.buyer_contact_number} onChange={updateOrderForm} required />
            </label>
            <label className="fs-field">
              <span>Delivery address</span>
              <textarea name="buyer_address" rows="3" value={orderForm.buyer_address} onChange={updateOrderForm} required />
            </label>
            <label className="fs-field">
              <span>Note (optional)</span>
              <textarea name="buyer_note" rows="2" value={orderForm.buyer_note} onChange={updateOrderForm} />
            </label>

            <div className="fs-slip-actions">
              <button type="button" className="fs-cancel-button" onClick={() => setCartOpen(false)}>Continue shopping</button>
              <button type="submit" className="fs-submit-button" disabled={orderSaving}>
                {orderSaving ? 'Sending…' : 'Order all items'}
              </button>
            </div>
              </>
            ) : (
              <div className="fs-cart-empty">
                <span aria-hidden="true">🛒</span>
                <p>Your cart is empty.</p>
                <button type="button" className="fs-submit-button" onClick={() => setCartOpen(false)}>Browse fish</button>
              </div>
            )}
          </form>
        </div>
      )}
    </div>
  );
}
