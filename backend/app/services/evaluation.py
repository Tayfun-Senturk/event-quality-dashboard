from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Alert, EvaluationResult, RawEvent

EXPECTED_METRICS_BY_ANOMALY_TYPE = {
    "duplicate": {"duplicate_count", "duplicate_ratio"},
    "missing_fields": {"missing_field_ratio"},
    "invalid_values": {"invalid_value_count"},
    "spike": {"event_count"},
    "drop": {"event_count"},
}


def calculate_and_store_evaluation(db: Session) -> EvaluationResult:
    db.query(EvaluationResult).delete()

    injected_units = _injected_anomaly_units(db)
    alerts = db.query(Alert).all()

    detected_units = 0
    for bucket, anomaly_type in injected_units:
        expected_metrics = EXPECTED_METRICS_BY_ANOMALY_TYPE.get(anomaly_type, set())
        if any(alert.time_bucket == bucket and alert.metric_name in expected_metrics for alert in alerts):
            detected_units += 1

    false_alarm_count = 0
    for alert in alerts:
        if not _alert_matches_injected_unit(alert, injected_units):
            false_alarm_count += 1

    injected_count = len(injected_units)
    total_alert_count = len(alerts)
    detection_rate = detected_units / injected_count if injected_count else None
    false_alarm_rate = false_alarm_count / total_alert_count if total_alert_count else 0.0

    result = EvaluationResult(
        detection_rate=detection_rate,
        false_alarm_rate=false_alarm_rate,
        injected_anomaly_count=injected_count,
        detected_anomaly_count=detected_units,
        false_alarm_count=false_alarm_count,
        total_alert_count=total_alert_count,
    )
    db.add(result)
    db.flush()
    return result


def _injected_anomaly_units(db: Session) -> set[tuple]:
    rows = (
        db.query(RawEvent.time_bucket, RawEvent.injected_anomaly_type)
        .filter(RawEvent.is_injected_anomaly.is_(True), RawEvent.injected_anomaly_type.isnot(None))
        .distinct()
        .all()
    )
    return {(time_bucket, anomaly_type) for time_bucket, anomaly_type in rows if anomaly_type}


def _alert_matches_injected_unit(alert: Alert, injected_units: set[tuple]) -> bool:
    for bucket, anomaly_type in injected_units:
        expected_metrics = EXPECTED_METRICS_BY_ANOMALY_TYPE.get(anomaly_type, set())
        if alert.time_bucket == bucket and alert.metric_name in expected_metrics:
            return True
    return False
