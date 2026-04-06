import { useState, useEffect } from 'react';
import { useSSE } from '../hooks/useSSE';
import { api } from '../services/api';
import DeviceCard from '../components/DeviceCard';
import PowerChart from '../components/PowerChart';
import { formatPower } from '../utils/formatters';

export default function Dashboard() {
  const { liveData, isConnected } = useSSE();
  const [initialData, setInitialData] = useState(null);
  const [recentReadings, setRecentReadings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch initial dashboard data on mount
    api.getCurrentReadings()
      .then((data) => {
        setInitialData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load initial data:', err);
        setLoading(false);
      });
  }, []);

  // Use live data if available, otherwise use initial data
  const dashboardData = liveData?.readings || initialData;

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>Loading dashboard...</div>;
  }

  const devices = dashboardData?.devices || [];
  const unknownLoad = dashboardData?.unknown_load_watts;

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#111827', marginBottom: '8px' }}>Energy Dashboard</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>Real-time monitoring</span>
          {isConnected && <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#10b981' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />Live</span>}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {devices.map((device) => <DeviceCard key={device.device_id} device={device} isLive={isConnected} />)}
      </div>
      {unknownLoad !== null && unknownLoad !== undefined && <div style={{ border: '2px dashed #f59e0b', borderRadius: '8px', padding: '16px', backgroundColor: '#fffbeb', marginBottom: '24px' }}><div style={{ fontSize: '14px', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>⚠️ Unknown Load</div><div style={{ fontSize: '24px', fontWeight: '700', color: '#111827' }}>{formatPower(unknownLoad)}</div><div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Difference between main meter and smart plugs</div></div>}
      <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '20px', backgroundColor: '#ffffff' }}><h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>Current Power Readings</h2><div style={{ color: '#6b7280', fontSize: '14px' }}>Live data updates every 5 seconds via SSE stream</div></div>
    </div>
  );
}
