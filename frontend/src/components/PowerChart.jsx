import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatTime } from '../utils/formatters';

export default function PowerChart({ data, height = 300 }) {
  if (!data || data.length === 0) {
    return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>No data available</div>;
  }

  const chartData = data.map((reading) => ({
    time: formatTime(reading.timestamp),
    'Main Meter': reading.main_meter || 0,
    AC: reading.ac || 0,
    Geyser: reading.geyser || 0,
    Pump: reading.pump || 0,
    'Unknown Load': reading.unknown_load || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="time" stroke="#6b7280" style={{ fontSize: '12px' }} interval="preserveStartEnd" />
        <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} label={{ value: 'Power (W)', angle: -90, position: 'insideLeft' }} />
        <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '12px' }} />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        <Line type="monotone" dataKey="Main Meter" stroke="#8b5cf6" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="AC" stroke="#3b82f6" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Geyser" stroke="#ef4444" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Pump" stroke="#10b981" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Unknown Load" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
