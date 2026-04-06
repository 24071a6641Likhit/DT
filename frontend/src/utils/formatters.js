export const formatPower = (watts) => {
  if (watts === null || watts === undefined) return 'N/A';
  if (watts >= 1000) return `${(watts / 1000).toFixed(2)} kW`;
  return `${watts.toFixed(0)} W`;
};

export const formatEnergy = (kwh) => {
  if (kwh === null || kwh === undefined) return 'N/A';
  return `${kwh.toFixed(2)} kWh`;
};

export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return 'N/A';
  return `₹${amount.toFixed(2)}`;
};

export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

export const formatTime = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

export const getDeviceIcon = (deviceType) => {
  const icons = {
    main_meter: '⚡',
    smart_plug: '🔌',  // Generic smart plug icon - all plugs use same type
  };
  return icons[deviceType] || '🔌';
};

export const getSeverityColor = (severity) => {
  const colors = {
    info: '#3b82f6',
    warning: '#f59e0b',
    critical: '#ef4444',
  };
  return colors[severity] || '#6b7280';
};

export const getSeverityBadge = (severity) => {
  const badges = {
    info: { bg: '#dbeafe', text: '#1e40af' },
    warning: { bg: '#fef3c7', text: '#92400e' },
    critical: { bg: '#fee2e2', text: '#991b1b' },
  };
  return badges[severity] || { bg: '#f3f4f6', text: '#374151' };
};
