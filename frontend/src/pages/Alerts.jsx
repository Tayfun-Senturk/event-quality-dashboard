import { useEffect, useMemo, useState } from 'react';

import { getAlerts } from '../api/client.js';
import { formatDateTime } from '../utils/formatters.js';

function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadAlerts() {
      try {
        setLoading(true);
        setError('');
        setAlerts(await getAlerts());
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadAlerts();
  }, []);

  const filteredAlerts = useMemo(() => {
    if (severityFilter === 'all') {
      return alerts;
    }

    return alerts.filter((alert) => alert.severity === severityFilter);
  }, [alerts, severityFilter]);

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Alerts</p>
        <h2>Anomaly alert list</h2>
        <p>Review generated alerts sorted newest first, including metric, method, severity, and reason.</p>
      </div>

      {error ? <div className="alert-banner error">{error}</div> : null}

      <div className="toolbar">
        <label htmlFor="severity-filter">Severity</label>
        <select
          disabled={!alerts.length}
          id="severity-filter"
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value)}
        >
          <option value="all">All</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="table-panel">
        <h3>Generated Alerts</h3>
        {loading ? (
          <div className="state-panel">Loading alerts...</div>
        ) : filteredAlerts.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Metric</th>
                  <th>Anomaly Type</th>
                  <th>Time Bucket</th>
                  <th>Reason</th>
                  <th>Created At</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <span className={`severity-pill ${alert.severity}`}>{alert.severity}</span>
                    </td>
                    <td>{alert.metric_name}</td>
                    <td>{alert.anomaly_type}</td>
                    <td>{alert.time_bucket}</td>
                    <td>{alert.reason}</td>
                    <td>{formatDateTime(alert.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            {alerts.length ? 'No alerts match the selected severity.' : 'No alerts yet. Inject an anomaly and run analysis from the Overview page.'}
          </div>
        )}
      </div>
    </section>
  );
}

export default Alerts;
