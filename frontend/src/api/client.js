const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function healthCheck() {
  return request('/health');
}

export function seedData(days = 14, eventsPerDay = 100) {
  return request('/seed', {
    method: 'POST',
    body: JSON.stringify({
      days,
      events_per_day: eventsPerDay,
    }),
  });
}

export function injectAnomaly(anomalyType, amount) {
  const payload = { anomaly_type: anomalyType };

  if (amount !== undefined && amount !== null) {
    payload.amount = amount;
  }

  return request('/anomalies/inject', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function runAnalysis() {
  return request('/analyze', {
    method: 'POST',
  });
}

export function resetDemoData() {
  return request('/reset', {
    method: 'POST',
  });
}

export function getSummary() {
  return request('/summary');
}

export function getMetrics() {
  return request('/metrics');
}

export function getAlerts() {
  return request('/alerts');
}

export function getEvaluation() {
  return request('/evaluation');
}
