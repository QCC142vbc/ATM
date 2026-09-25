const API_BASE = '/api';

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const options = {
    method,
    credentials: 'include',
    headers: { ...headers },
  };

  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    let errorPayload = {};
    try {
      errorPayload = await response.json();
    } catch {
      errorPayload = { error: { message: 'Request failed' } };
    }

    const detail = errorPayload?.detail;
    const extractedError = typeof detail === 'object' && detail !== null ? detail.error ?? detail : errorPayload?.error ?? {};
    const message = extractedError.message || detail?.message || errorPayload?.message || 'Request failed';
    const error = new Error(message);
    error.payload = extractedError && Object.keys(extractedError).length ? { error: extractedError } : errorPayload;
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  login: (userId, pin) => request('/auth/login', { method: 'POST', body: { user_id: userId, pin } }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  session: () => request('/auth/session'),
  getAccount: () => request('/account'),
  getTransactions: () => request('/transactions'),
  deposit: (amount) => request('/account/deposit', { method: 'POST', body: { amount: String(amount) } }),
  withdraw: (amount) => request('/account/withdraw', { method: 'POST', body: { amount: String(amount) } }),
  transfer: ({ recipientId, amount, description }) => request('/transfers', {
    method: 'POST',
    body: { recipient_id: recipientId, amount: String(amount), description },
  }),
  changePin: ({ currentPin, newPin, confirmPin }) => request('/auth/change-pin', {
    method: 'POST',
    body: { current_pin: currentPin, new_pin: newPin, confirm_pin: confirmPin },
  }),
  getAtmCash: () => request('/atm/cash'),
  atmWithdraw: (amount) => request('/atm/withdraw', { method: 'POST', body: { amount: String(amount) } }),
}
