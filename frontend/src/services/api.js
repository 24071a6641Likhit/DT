// API service for backend communication
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // Dashboard
  getCurrentReadings: async () => {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/current`);
    if (!response.ok) throw new Error('Failed to fetch current readings');
    return response.json();
  },

  getRecentReadings: async (minutes = 30) => {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/recent?minutes=${minutes}`);
    if (!response.ok) throw new Error('Failed to fetch recent readings');
    return response.json();
  },

  // Devices
  getDevices: async () => {
    const response = await fetch(`${API_BASE_URL}/api/devices`);
    if (!response.ok) throw new Error('Failed to fetch devices');
    return response.json();
  },

  updateDevice: async (deviceId, data) => {
    const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update device');
    return response.json();
  },

  // Alerts
  getAlerts: async (params = {}) => {
    const queryParams = new URLSearchParams(params);
    const response = await fetch(`${API_BASE_URL}/api/alerts?${queryParams}`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  },

  getAlertCount: async () => {
    const response = await fetch(`${API_BASE_URL}/api/alerts/count`);
    if (!response.ok) throw new Error('Failed to fetch alert count');
    return response.json();
  },

  acknowledgeAlert: async (alertId) => {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to acknowledge alert');
    return response.json();
  },

  // Billing
  getCurrentMonthBill: async () => {
    const response = await fetch(`${API_BASE_URL}/api/billing/current-month`);
    if (!response.ok) throw new Error('Failed to fetch current month bill');
    return response.json();
  },

  getMonthlyComparison: async (months = 6) => {
    const response = await fetch(`${API_BASE_URL}/api/billing/monthly-comparison?months=${months}`);
    if (!response.ok) throw new Error('Failed to fetch monthly comparison');
    return response.json();
  },

  getSlabRates: async () => {
    const response = await fetch(`${API_BASE_URL}/api/billing/rates`);
    if (!response.ok) throw new Error('Failed to fetch slab rates');
    return response.json();
  },

  // Historical
  getDailySummaries: async (startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await fetch(`${API_BASE_URL}/api/historical/daily?${params}`);
    if (!response.ok) throw new Error('Failed to fetch daily summaries');
    return response.json();
  },

  getHourlySummaries: async (deviceId, date) => {
    const params = new URLSearchParams({ device_id: deviceId, date });
    const response = await fetch(`${API_BASE_URL}/api/historical/hourly?${params}`);
    if (!response.ok) throw new Error('Failed to fetch hourly summaries');
    return response.json();
  },
};

// SSE connection for real-time updates
export const createSSEConnection = (onMessage, onError) => {
  const eventSource = new EventSource(`${API_BASE_URL}/api/stream/live`);

  eventSource.addEventListener('readings', (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage('readings', data);
    } catch (error) {
      console.error('Failed to parse readings event:', error);
    }
  });

  eventSource.addEventListener('alert', (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage('alert', data);
    } catch (error) {
      console.error('Failed to parse alert event:', error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);
    if (onError) onError(error);
  };

  return eventSource;
};
