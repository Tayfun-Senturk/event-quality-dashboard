from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from app.models import Alert, MetricSnapshot

MOVING_AVERAGE_WINDOW = 3
MOVING_AVERAGE_DEVIATION_THRESHOLD = 0.5
ZSCORE_THRESHOLD = 2.0
MIN_CHANGE_BY_METRIC = {
    "missing_field_ratio": 0.05,
    "duplicate_count": 3.0,
    "duplicate_ratio": 0.03,
    "invalid_value_count": 3.0,
    "event_count": 20.0,
    "schema_drift_flag": 1.0,
}


def detect_and_store_alerts(db: Session, snapshots: list[MetricSnapshot]) -> list[Alert]:
    grouped_snapshots: dict[str, list[MetricSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        grouped_snapshots[snapshot.metric_name].append(snapshot)

    alerts: list[Alert] = []
    for metric_name, metric_snapshots in grouped_snapshots.items():
        ordered_snapshots = sorted(metric_snapshots, key=lambda item: item.time_bucket)
        previous_values: list[float] = []

        for snapshot in ordered_snapshots:
            moving_average_alert = _moving_average_alert(metric_name, snapshot.value, previous_values)
            zscore_alert = _zscore_alert(metric_name, snapshot.value, previous_values)

            detection_methods: list[str] = []
            if moving_average_alert is not None:
                detection_methods.append("moving_average")
                alerts.append(_build_alert(snapshot, moving_average_alert))
            if zscore_alert is not None:
                detection_methods.append("z_score")
                alerts.append(_build_alert(snapshot, zscore_alert))

            if detection_methods:
                snapshot.is_anomaly = True
                snapshot.detection_method = ",".join(detection_methods)

            previous_values.append(snapshot.value)

    db.add_all(alerts)
    db.flush()
    return alerts


def _moving_average_alert(metric_name: str, value: float, previous_values: list[float]) -> dict | None:
    if len(previous_values) < MOVING_AVERAGE_WINDOW:
        return None

    baseline_values = previous_values[-MOVING_AVERAGE_WINDOW:]
    baseline = mean(baseline_values)
    min_change = MIN_CHANGE_BY_METRIC.get(metric_name, 1.0)
    absolute_change = abs(value - baseline)

    if baseline == 0:
        is_anomaly = absolute_change >= min_change
        deviation = float("inf") if is_anomaly else 0.0
    else:
        deviation = absolute_change / abs(baseline)
        is_anomaly = deviation >= MOVING_AVERAGE_DEVIATION_THRESHOLD and absolute_change >= min_change

    if not is_anomaly:
        return None

    severity = "high" if deviation == float("inf") or deviation >= 1.0 else "medium"
    return {
        "anomaly_type": "moving_average",
        "severity": severity,
        "reason": (
            f"{metric_name} value {value:.4f} differs from the previous "
            f"{MOVING_AVERAGE_WINDOW}-day average {baseline:.4f}."
        ),
    }


def _zscore_alert(metric_name: str, value: float, previous_values: list[float]) -> dict | None:
    if len(previous_values) < MOVING_AVERAGE_WINDOW:
        return None

    baseline = mean(previous_values)
    standard_deviation = pstdev(previous_values)
    min_change = MIN_CHANGE_BY_METRIC.get(metric_name, 1.0)
    absolute_change = abs(value - baseline)

    if standard_deviation == 0:
        if absolute_change < min_change:
            return None
        z_score = float("inf")
    else:
        z_score = abs((value - baseline) / standard_deviation)
        if z_score < ZSCORE_THRESHOLD or absolute_change < min_change:
            return None

    severity = "high" if z_score == float("inf") or z_score >= 3.0 else "medium"
    z_score_label = "infinite" if z_score == float("inf") else f"{z_score:.2f}"
    return {
        "anomaly_type": "z_score",
        "severity": severity,
        "reason": f"{metric_name} value {value:.4f} has z-score {z_score_label} against previous buckets.",
    }


def _build_alert(snapshot: MetricSnapshot, alert_data: dict) -> Alert:
    return Alert(
        metric_name=snapshot.metric_name,
        anomaly_type=alert_data["anomaly_type"],
        severity=alert_data["severity"],
        time_bucket=snapshot.time_bucket,
        reason=alert_data["reason"],
    )
