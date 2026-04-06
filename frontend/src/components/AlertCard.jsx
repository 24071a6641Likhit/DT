import { formatDateTime, getSeverityBadge } from '../utils/formatters';

export default function AlertCard({ alert, onAcknowledge }) {
  // FIX: Use correct field names from backend API
  const { id, alert_type, severity, message, actual_value, threshold_value, timestamp, is_acknowledged } = alert;
  const badge = getSeverityBadge(severity);

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '16px', backgroundColor: is_acknowledged ? '#f9fafb' : '#ffffff', opacity: is_acknowledged ? 0.6 : 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600', backgroundColor: badge.bg, color: badge.text }}>{severity.toUpperCase()}</span>
            <span style={{ fontSize: '12px', color: '#6b7280' }}>{alert_type.replace('_', ' ').toUpperCase()}</span>
          </div>
          <div style={{ fontSize: '14px', color: '#111827', marginBottom: '8px' }}>{message}</div>
          {actual_value !== null && threshold_value !== null && <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>Value: {actual_value.toFixed(0)} W | Threshold: {threshold_value.toFixed(0)} W</div>}
          <div style={{ fontSize: '12px', color: '#6b7280' }}>{formatDateTime(timestamp)}</div>
        </div>
        {!is_acknowledged && onAcknowledge && <button onClick={() => onAcknowledge(id)} style={{ padding: '6px 12px', backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', borderRadius: '4px', fontSize: '12px', fontWeight: '500', cursor: 'pointer' }}>Acknowledge</button>}
        {is_acknowledged && <span style={{ padding: '6px 12px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '4px', fontSize: '12px', fontWeight: '500' }}>✓ Acknowledged</span>}
      </div>
    </div>
  );
}
