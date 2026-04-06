import { formatPower, formatEnergy, getDeviceIcon } from '../utils/formatters';

export default function DeviceCard({ device, isLive = false }) {
  const { device_type, device_name, power_watts, cumulative_kwh, is_online } = device;

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '16px', backgroundColor: is_online ? '#ffffff' : '#f9fafb', position: 'relative' }}>
      {isLive && <div style={{ position: 'absolute', top: '12px', right: '12px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981', animation: 'pulse 2s infinite' }} />}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <span style={{ fontSize: '32px' }}>{getDeviceIcon(device_type)}</span>
        <div>
          <div style={{ fontWeight: '600', fontSize: '16px', color: '#111827' }}>{device_name}</div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>{device_type.replace('_', ' ').toUpperCase()}</div>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Current Power</div>
          <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827' }}>{formatPower(power_watts)}</div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Energy</div>
          <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827' }}>{formatEnergy(cumulative_kwh)}</div>
        </div>
      </div>
      {!is_online && <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '4px', fontSize: '12px', textAlign: 'center' }}>⚠️ Offline</div>}
    </div>
  );
}
