import { useState, useEffect } from 'react';
import { alertsApi } from '../services/api';

export const useAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await alertsApi.getAlerts();
      setAlerts(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlerts = async (alertIds, note, acknowledgedBy) => {
    try {
      // Save username to localStorage for next time
      if (acknowledgedBy) {
        localStorage.setItem('alertManager_username', acknowledgedBy);
      }
      
      await alertsApi.acknowledgeAlerts(alertIds, note, acknowledgedBy);
      await fetchAlerts(); // Refresh alerts
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const resolveAlerts = async (alertIds, note, resolvedBy) => {
    try {
      // Save username to localStorage for next time
      if (resolvedBy) {
        localStorage.setItem('alertManager_username', resolvedBy);
      }
      
      await alertsApi.resolveAlerts(alertIds, note, resolvedBy);
      await fetchAlerts(); // Refresh alerts
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const syncAlerts = async () => {
    try {
      await alertsApi.syncAlerts();
      await fetchAlerts(); // Refresh alerts
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  useEffect(() => {
    fetchAlerts();
    
    // Auto-refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    alerts,
    loading,
    error,
    fetchAlerts,
    acknowledgeAlerts,
    resolveAlerts,
    syncAlerts,
  };
};