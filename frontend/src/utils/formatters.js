export function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '--';
  }

  return new Intl.NumberFormat('en-US').format(Number(value));
}

export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '--';
  }

  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function formatMetricValue(metricName, value) {
  if (metricName.includes('ratio') || metricName === 'missing_field_ratio') {
    return formatPercent(value);
  }

  return Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 3);
}

export function formatDateTime(value) {
  if (!value) {
    return '--';
  }

  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function formatMetricLabel(value) {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
