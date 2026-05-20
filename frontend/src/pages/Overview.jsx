import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  getMetrics,
  getSummary,
  injectAnomaly,
  resetDemoData,
  runAnalysis,
  seedData,
} from '../api/client.js';
import { formatDateTime, formatMetricValue, formatNumber, formatPercent } from '../utils/formatters.js';

const anomalyActions = [
  { label: 'Inject Duplicate Anomaly', type: 'duplicate', amount: 25 },
  { label: 'Inject Missing Fields Anomaly', type: 'missing_fields', amount: 25 },
  { label: 'Inject Invalid Values Anomaly', type: 'invalid_values', amount: 25 },
  { label: 'Inject Spike Anomaly', type: 'spike' },
  { label: 'Inject Drop Anomaly', type: 'drop' },
];

function Overview() {
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const refreshDashboard = useCallback(async () => {
    setError('');
    const [summaryData, metricsData] = await Promise.all([getSummary(), getMetrics()]);
    setSummary(summaryData);
    setMetrics(metricsData);
  }, []);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        await refreshDashboard();
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();
  }, [refreshDashboard]);

  const eventCountData = useMemo(
    () =>
      metrics
        .filter((metric) => metric.metric_name === 'event_count')
        .map((metric) => ({
          time_bucket: metric.time_bucket,
          value: metric.value,
          is_anomaly: metric.is_anomaly,
        })),
    [metrics],
  );

  async function runAction(actionName, action) {
    try {
      setActionLoading(actionName);
      setError('');
      setMessage('');
      const result = await action();
      await refreshDashboard();
      setMessage(buildActionMessage(actionName, result));
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setActionLoading('');
    }
  }

  if (loading) {
    return <PageState title="Loading dashboard data..." />;
  }

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Overview</p>
        <h2>Data quality monitoring snapshot</h2>
        <p>Run the backend demo flow and review the latest metric and alert state from PostgreSQL.</p>
      </div>

      <div className="workflow-panel">
        <strong>Demo workflow</strong>
        <span>1. Seed Data</span>
        <span>2. Inject Anomaly</span>
        <span>3. Run Analysis</span>
        <span>4. Review Dashboard / Alerts / Evaluation</span>
        <span>Use Reset Demo Data to start again</span>
      </div>

      {error ? <div className="alert-banner error">{error}</div> : null}
      {message ? <div className="alert-banner success">{message}</div> : null}

      <div className="action-grid">
        <button
          className="primary-button"
          disabled={Boolean(actionLoading)}
          type="button"
          onClick={() => runAction('seed', () => seedData())}
        >
          {actionLoading === 'seed' ? 'Seeding...' : 'Seed Data'}
        </button>
        {anomalyActions.map((action) => (
          <button
            className="secondary-button"
            disabled={Boolean(actionLoading)}
            key={action.type}
            type="button"
            onClick={() => runAction(action.type, () => injectAnomaly(action.type, action.amount))}
          >
            {actionLoading === action.type ? 'Injecting...' : action.label}
          </button>
        ))}
        <button
          className="primary-button"
          disabled={Boolean(actionLoading)}
          type="button"
          onClick={() => runAction('analysis', () => runAnalysis())}
        >
          {actionLoading === 'analysis' ? 'Analyzing...' : 'Run Analysis'}
        </button>
        <button
          className="secondary-button"
          disabled={Boolean(actionLoading)}
          type="button"
          onClick={() => runAction('refresh', () => refreshDashboard())}
        >
          {actionLoading === 'refresh' ? 'Refreshing...' : 'Refresh Dashboard'}
        </button>
        <button
          className="danger-button"
          disabled={Boolean(actionLoading)}
          type="button"
          onClick={() => runAction('reset', () => resetDemoData())}
        >
          {actionLoading === 'reset' ? 'Resetting...' : 'Reset Demo Data'}
        </button>
      </div>

      <div className="metric-grid six-columns">
        <MetricCard label="Total Events" value={formatNumber(summary?.total_events)} />
        <MetricCard label="Total Alerts" value={formatNumber(summary?.total_alerts)} />
        <MetricCard label="Latest Missing Field Ratio" value={formatPercent(summary?.missing_field_ratio)} />
        <MetricCard label="Latest Duplicate Ratio" value={formatPercent(summary?.duplicate_ratio)} />
        <MetricCard label="Latest Invalid Value Count" value={formatNumber(summary?.invalid_value_count)} />
        <MetricCard label="Latest Event Count" value={formatNumber(summary?.latest_event_count)} />
      </div>

      <div className="content-grid">
        <div className="chart-panel">
          <h3>Event Count Trend</h3>
          {eventCountData.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={eventCountData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time_bucket" />
                <YAxis />
                <Tooltip formatter={(value) => [formatMetricValue('event_count', value), 'Event Count']} />
                <Line
                  dataKey="value"
                  dot={(props) => <AnomalyDot {...props} />}
                  name="Event Count"
                  stroke="#2563eb"
                  strokeWidth={2}
                  type="monotone"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="No event_count metric snapshots yet. Seed data and run analysis first." />
          )}
        </div>

        <div className="list-panel">
          <h3>Recent Alerts</h3>
          {summary?.latest_alerts?.length ? (
            <div className="compact-list">
              {summary.latest_alerts.map((alert) => (
                <article className="compact-list-item" key={alert.id}>
                  <div>
                    <span className={`severity-pill ${alert.severity}`}>{alert.severity}</span>
                    <strong>{alert.metric_name}</strong>
                  </div>
                  <p>{alert.reason}</p>
                  <small>{alert.time_bucket} - {formatDateTime(alert.created_at)}</small>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState message="No alerts yet. Inject an anomaly and run analysis." />
          )}
        </div>
      </div>
    </section>
  );
}

function MetricCard({ label, value }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function PageState({ title }) {
  return (
    <section className="page">
      <div className="state-panel">{title}</div>
    </section>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

function AnomalyDot(props) {
  const { cx, cy, payload } = props;
  const color = payload?.is_anomaly ? '#dc2626' : '#2563eb';

  return <circle cx={cx} cy={cy} fill={color} r={payload?.is_anomaly ? 5 : 3} stroke="#ffffff" strokeWidth={2} />;
}

function buildActionMessage(actionName, result) {
  if (actionName === 'seed') {
    return `Seeded ${formatNumber(result.inserted_event_count)} synthetic events.`;
  }

  if (actionName === 'analysis') {
    return `Analysis completed: ${formatNumber(result.metric_snapshot_count)} metric snapshots and ${formatNumber(result.generated_alert_count)} alerts.`;
  }

  if (actionName === 'refresh') {
    return 'Dashboard refreshed.';
  }

  if (actionName === 'reset') {
    return `Reset completed: deleted ${formatNumber(result.deleted_raw_events)} raw events, ${formatNumber(result.deleted_metric_snapshots)} metric snapshots, ${formatNumber(result.deleted_alerts)} alerts, and ${formatNumber(result.deleted_evaluation_results)} evaluation rows.`;
  }

  return `Injected ${formatNumber(result.inserted_event_count)} ${result.anomaly_type} events.`;
}

export default Overview;
