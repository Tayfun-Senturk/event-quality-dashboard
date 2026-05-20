import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { getMetrics } from '../api/client.js';
import { formatMetricLabel, formatMetricValue } from '../utils/formatters.js';

function MetricDetail() {
  const [metrics, setMetrics] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('event_count');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError('');
        const data = await getMetrics();
        const metricNames = [...new Set(data.map((metric) => metric.metric_name))];
        setMetrics(data);
        setSelectedMetric((current) => {
          if (metricNames.includes(current)) {
            return current;
          }

          return metricNames[0] ?? 'event_count';
        });
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  const metricNames = useMemo(
    () => [...new Set(metrics.map((metric) => metric.metric_name))].sort(),
    [metrics],
  );

  const selectedSnapshots = useMemo(
    () => metrics.filter((metric) => metric.metric_name === selectedMetric),
    [metrics, selectedMetric],
  );

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Metric Detail</p>
        <h2>Metric history and anomaly markers</h2>
        <p>Inspect daily metric snapshots and anomaly states calculated by the backend analysis step.</p>
      </div>

      {error ? <div className="alert-banner error">{error}</div> : null}

      <div className="toolbar">
        <label htmlFor="metric-select">Metric</label>
        <select
          disabled={!metricNames.length}
          id="metric-select"
          value={selectedMetric}
          onChange={(event) => setSelectedMetric(event.target.value)}
        >
          {metricNames.map((metricName) => (
            <option key={metricName} value={metricName}>
              {formatMetricLabel(metricName)}
            </option>
          ))}
        </select>
      </div>

      <div className="chart-panel">
        <h3>{formatMetricLabel(selectedMetric)} Trend</h3>
        {loading ? (
          <div className="state-panel">Loading metric snapshots...</div>
        ) : selectedSnapshots.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={selectedSnapshots} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time_bucket" />
              <YAxis />
              <Tooltip formatter={(value) => [formatMetricValue(selectedMetric, value), selectedMetric]} />
              <Line
                dataKey="value"
                dot={(props) => <AnomalyDot {...props} />}
                name={selectedMetric}
                stroke="#0f766e"
                strokeWidth={2}
                type="monotone"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">No metric snapshots available. Seed data and run analysis first.</div>
        )}
      </div>

      <div className="table-panel">
        <h3>Metric Snapshots</h3>
        {selectedSnapshots.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time Bucket</th>
                  <th>Metric</th>
                  <th>Value</th>
                  <th>Anomaly</th>
                  <th>Detection Method</th>
                </tr>
              </thead>
              <tbody>
                {selectedSnapshots.map((snapshot) => (
                  <tr key={snapshot.id}>
                    <td>{snapshot.time_bucket}</td>
                    <td>{snapshot.metric_name}</td>
                    <td>{formatMetricValue(snapshot.metric_name, snapshot.value)}</td>
                    <td>
                      <span className={snapshot.is_anomaly ? 'status-pill danger' : 'status-pill neutral'}>
                        {snapshot.is_anomaly ? 'Anomaly' : 'Normal'}
                      </span>
                    </td>
                    <td>{snapshot.detection_method ?? '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">No rows to display.</div>
        )}
      </div>
    </section>
  );
}

function AnomalyDot(props) {
  const { cx, cy, payload } = props;
  const color = payload?.is_anomaly ? '#dc2626' : '#0f766e';

  return <circle cx={cx} cy={cy} fill={color} r={payload?.is_anomaly ? 5 : 3} stroke="#ffffff" strokeWidth={2} />;
}

export default MetricDetail;
