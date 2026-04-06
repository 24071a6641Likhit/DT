import { useState, useEffect } from 'react';
import { api } from '../services/api';
import AlertCard from '../components/AlertCard';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState({ severity: '', acknowledged: '' });
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const params = {};
      if (filter.severity) params.severity = filter.severity;
      if (filter.acknowledged !== '') params.is_acknowledged = filter.acknowledged;
      const response = await api.getAlerts(params);
      // FIX: Extract alerts array from response object
      setAlerts(response.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, [filter]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>Loading alerts...</div>;

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#111827', marginBottom: '24px' }}>Alerts</h1>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <select value={filter.severity} onChange={(e) => setFilter({ ...filter, severity: e.target.value })} style={{ padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}><option value="">All Severities</option><option value="info">Info</option><option value="warning">Warning</option><option value="critical">Critical</option></select>
        <select value={filter.acknowledged} onChange={(e) => setFilter({ ...filter, acknowledged: e.target.value })} style={{ padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px' }}><option value="">All Status</option><option value="false">Unacknowledged</option><option value="true">Acknowledged</option></select>
        <button onClick={fetchAlerts} style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>Refresh</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {alerts.length === 0 ? <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280', border: '1px solid #e5e7eb', borderRadius: '8px' }}>No alerts found</div> : alerts.map((alert) => <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} />)}
      </div>
    </div>
  );
}
