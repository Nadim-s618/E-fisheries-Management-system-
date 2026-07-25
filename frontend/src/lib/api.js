const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
const TOKEN_KEY = 'e_fisheries_token';


function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}


function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}


function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}


function getErrorMessage(data) {
  if (!data) {
    return 'Something went wrong. Please try again.';
  }

  if (typeof data === 'string') {
    return data;
  }

  if (data.detail) {
    return data.detail;
  }

  if (data.non_field_errors) {
    return data.non_field_errors.join(' ');
  }

  const [firstKey] = Object.keys(data);
  const firstValue = data[firstKey];

  if (Array.isArray(firstValue)) {
    return firstValue.join(' ');
  }

  if (typeof firstValue === 'string') {
    return firstValue;
  }

  return 'Something went wrong. Please try again.';
}


async function request(path, options = {}) {
  const token = getStoredToken();
  const headers = {
    Accept: 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Token ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(data));
  }

  return data;
}


export function getHomepage() {
  return request('/homepage/');
}


export function login(credentials) {
  return request('/auth/login/', {
    method: 'POST',
    body: credentials,
  });
}


export function signup(account) {
  return request('/auth/signup/', {
    method: 'POST',
    body: account,
  });
}


export function getCurrentUser() {
  return request('/auth/me/');
}


export function logout() {
  return request('/auth/logout/', {
    method: 'POST',
  });
}


export function getPonds() {
  return request('/ponds/');
}


export function createPond(pond) {
  return request('/ponds/', {
    method: 'POST',
    body: pond,
  });
}


export function updatePond(id, pond) {
  return request(`/ponds/${id}/`, {
    method: 'PATCH',
    body: pond,
  });
}


export function deletePond(id) {
  return request(`/ponds/${id}/`, {
    method: 'DELETE',
  });
}


export function getWaterQualityDashboard(pondId) {
  return request(`/water-quality/dashboard/?pond=${pondId}`);
}


export function getWeatherDashboard(pondId, options = {}) {
  const params = new URLSearchParams();
  params.set('pond', pondId);
  if (options.refresh) params.set('refresh', '1');

  return request(`/weather/dashboard/?${params.toString()}`);
}


export function getWaterQualityReadings(filters = {}) {
  const params = new URLSearchParams();

  if (filters.pond) params.set('pond', filters.pond);
  if (filters.date) params.set('date', filters.date);
  if (filters.status) params.set('status', filters.status);

  const query = params.toString();
  return request(`/water-quality/water-quality-readings/${query ? `?${query}` : ''}`);
}


export function createWaterQualityReading(reading) {
  return request('/water-quality/water-quality-readings/', {
    method: 'POST',
    body: reading,
  });
}


export function getWaterQualityHistory(filters = {}) {
  const params = new URLSearchParams();

  if (filters.pond) params.set('pond', filters.pond);
  if (filters.period) params.set('period', filters.period);

  return request(`/water-quality/history/?${params.toString()}`);
}


export function getWaterQualityGraph(filters = {}) {
  const params = new URLSearchParams();

  if (filters.pond) params.set('pond', filters.pond);
  if (filters.period) params.set('period', filters.period);

  return request(`/water-quality/graph/?${params.toString()}`);
}


export function compareWaterQualityPonds(pondIds) {
  const params = new URLSearchParams();
  params.set('ponds', pondIds.join(','));

  return request(`/water-quality/compare/?${params.toString()}`);
}


export function getPondStocks(pondId) {
  return request(`/ponds/${pondId}/stocks/`);
}


export function createStock(pondId, stock) {
  return request(`/ponds/${pondId}/stocks/`, {
    method: 'POST',
    body: stock,
  });
}


export function updateStock(id, stock) {
  return request(`/stocks/${id}/`, {
    method: 'PATCH',
    body: stock,
  });
}


export function deleteStock(id) {
  return request(`/stocks/${id}/`, {
    method: 'DELETE',
  });
}


export function getStockGrowth(stockId) {
  return request(`/stocks/${stockId}/growth/`);
}


export function createGrowthRecord(stockId, growthRecord) {
  return request(`/stocks/${stockId}/growth/`, {
    method: 'POST',
    body: growthRecord,
  });
}


export function updateGrowthRecord(id, growthRecord) {
  return request(`/growth/${id}/`, {
    method: 'PATCH',
    body: growthRecord,
  });
}


export function deleteGrowthRecord(id) {
  return request(`/growth/${id}/`, {
    method: 'DELETE',
  });
}


export const authStorage = {
  getStoredToken,
  saveToken,
  clearToken,
};