import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const alertsApi = {
  getAlerts: (skip = 0, limit = 1000) => 
    api.get(`/api/alerts?skip=${skip}&limit=${limit}`),
  
  getAlert: (alertId) => 
    api.get(`/api/alerts/${alertId}`),
  
  acknowledgeAlerts: (alertIds, note, acknowledgedBy) => 
    api.post('/api/alerts/acknowledge', { 
      alert_ids: alertIds, 
      note,
      acknowledged_by: acknowledgedBy || 'System User'
    }),
  
  resolveAlerts: (alertIds, note, resolvedBy) => 
    api.post('/api/alerts/resolve', { 
      alert_ids: alertIds, 
      note,
      resolved_by: resolvedBy || 'System User'
    }),
  
  syncAlerts: () => 
    api.post('/api/alerts/sync'),

  // === CSV Export Functions ===
  exportCSV: (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.severity && filters.severity.length > 0) {
      filters.severity.forEach(s => params.append('severity', s));
    }
    if (filters.grafana_status && filters.grafana_status.length > 0) {
      filters.grafana_status.forEach(s => params.append('grafana_status', s));
    }
    if (filters.jira_status && filters.jira_status.length > 0) {
      filters.jira_status.forEach(s => params.append('jira_status', s));
    }
    if (filters.cluster) {
      params.append('cluster', filters.cluster);
    }
    if (filters.date_from) {
      params.append('date_from', filters.date_from);
    }
    if (filters.date_to) {
      params.append('date_to', filters.date_to);
    }
    if (filters.include_resolved !== undefined) {
      params.append('include_resolved', filters.include_resolved);
    }
    
    return api.get(`/api/alerts/export/csv?${params.toString()}`, {
      responseType: 'blob'
    });
  },
  
  getExportSummary: () => 
    api.get('/api/alerts/export/summary'),
};

export const configApi = {
  getCronConfigs: () => 
    api.get('/api/config/cron'),
  
  createCronConfig: (config) => 
    api.post('/api/config/cron', config),
  
  updateCronConfig: (configId, config) => 
    api.put(`/api/config/cron/${configId}`, config),
};

export default api;