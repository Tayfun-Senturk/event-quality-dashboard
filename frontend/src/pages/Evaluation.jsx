import { useEffect, useState } from 'react';

import { getEvaluation } from '../api/client.js';
import { formatNumber, formatPercent } from '../utils/formatters.js';

function Evaluation() {
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadEvaluation() {
      try {
        setLoading(true);
        setError('');
        setEvaluation(await getEvaluation());
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadEvaluation();
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Evaluation</p>
        <h2>Detection quality summary</h2>
        <p>Compare controlled anomaly labels with generated alerts to estimate detection quality for the MVP.</p>
      </div>

      {error ? <div className="alert-banner error">{error}</div> : null}

      {loading ? (
        <div className="state-panel">Loading evaluation...</div>
      ) : evaluation ? (
        <>
          <div className="metric-grid">
            <EvaluationCard label="Detection Rate" value={formatPercent(evaluation.detection_rate)} />
            <EvaluationCard label="False Alarm Rate" value={formatPercent(evaluation.false_alarm_rate)} />
            <EvaluationCard label="Injected Anomaly Count" value={formatNumber(evaluation.injected_anomaly_count)} />
            <EvaluationCard label="Detected Anomaly Count" value={formatNumber(evaluation.detected_anomaly_count)} />
            <EvaluationCard label="False Alarm Count" value={formatNumber(evaluation.false_alarm_count)} />
            <EvaluationCard label="Total Alert Count" value={formatNumber(evaluation.total_alert_count)} />
          </div>

          <div className="info-panel">
            <h3>How to read this evaluation</h3>
            <p>
              Detection rate is the share of injected anomaly buckets that produced a matching alert. False alarm rate is
              the share of alerts that do not match an injected anomaly label. These values are simple MVP indicators,
              not a production-grade model evaluation.
            </p>
          </div>
        </>
      ) : (
        <div className="empty-state">No evaluation result yet. Run analysis after injecting anomalies.</div>
      )}
    </section>
  );
}

function EvaluationCard({ label, value }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

export default Evaluation;
