from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models import MetricSnapshot, RawEvent
from app.services.synthetic_events import EXPECTED_PAYLOAD_KEYS, VALID_DEVICE_TYPES, VALID_EVENT_TYPES


def calculate_and_store_metric_snapshots(db: Session) -> list[MetricSnapshot]:
    db.query(MetricSnapshot).delete()

    events_by_bucket: dict[date, list[RawEvent]] = defaultdict(list)
    for event in db.query(RawEvent).order_by(RawEvent.time_bucket.asc(), RawEvent.id.asc()).all():
        events_by_bucket[event.time_bucket].append(event)

    snapshots: list[MetricSnapshot] = []
    for bucket in sorted(events_by_bucket):
        metrics = calculate_bucket_metrics(events_by_bucket[bucket])
        for metric_name, value in metrics.items():
            snapshot = MetricSnapshot(
                metric_name=metric_name,
                value=float(value),
                time_bucket=bucket,
                is_anomaly=False,
            )
            db.add(snapshot)
            snapshots.append(snapshot)

    db.flush()
    return snapshots


def calculate_bucket_metrics(events: list[RawEvent]) -> dict[str, float]:
    event_count = len(events)
    if event_count == 0:
        return {
            "missing_field_ratio": 0.0,
            "duplicate_count": 0.0,
            "duplicate_ratio": 0.0,
            "invalid_value_count": 0.0,
            "event_count": 0.0,
            "schema_drift_flag": 0.0,
        }

    missing_field_count = sum(1 for event in events if _has_missing_required_field(event))
    duplicate_count = _duplicate_count(events)
    invalid_value_count = sum(1 for event in events if _has_invalid_enum_value(event))
    schema_drift_flag = 1.0 if any(_has_schema_drift(event) for event in events) else 0.0

    return {
        "missing_field_ratio": missing_field_count / event_count,
        "duplicate_count": float(duplicate_count),
        "duplicate_ratio": duplicate_count / event_count,
        "invalid_value_count": float(invalid_value_count),
        "event_count": float(event_count),
        "schema_drift_flag": schema_drift_flag,
    }


def latest_metric_values(snapshots: list[MetricSnapshot]) -> dict[str, float]:
    if not snapshots:
        return {}

    latest_bucket = max(snapshot.time_bucket for snapshot in snapshots)
    return {
        snapshot.metric_name: snapshot.value
        for snapshot in snapshots
        if snapshot.time_bucket == latest_bucket
    }


def _has_missing_required_field(event: RawEvent) -> bool:
    required_values = [event.event_id, event.user_id, event.event_type, event.device_type, event.event_timestamp]
    return any(value is None or value == "" for value in required_values)


def _duplicate_count(events: list[RawEvent]) -> int:
    counts = Counter(event.event_id for event in events)
    return sum(count - 1 for count in counts.values() if count > 1)


def _has_invalid_enum_value(event: RawEvent) -> bool:
    invalid_event_type = event.event_type is not None and event.event_type not in VALID_EVENT_TYPES
    invalid_device_type = event.device_type is not None and event.device_type not in VALID_DEVICE_TYPES
    return invalid_event_type or invalid_device_type


def _has_schema_drift(event: RawEvent) -> bool:
    payload = event.payload or {}
    return any(key not in EXPECTED_PAYLOAD_KEYS for key in payload)
