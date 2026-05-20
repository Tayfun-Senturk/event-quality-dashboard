from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import RawEvent

VALID_EVENT_TYPES = ["page_view", "click", "purchase", "signup", "add_to_cart"]
VALID_DEVICE_TYPES = ["web", "mobile", "tablet"]
EXPECTED_PAYLOAD_KEYS = {"source", "campaign", "amount"}
DEFAULT_SEED_DAYS = 14
DEFAULT_EVENTS_PER_DAY = 100
DEFAULT_INJECTION_AMOUNT = 20


def seed_events(db: Session, days: int = DEFAULT_SEED_DAYS, events_per_day: int = DEFAULT_EVENTS_PER_DAY) -> int:
    end_day = datetime.now(timezone.utc).date() - timedelta(days=1)
    start_day = end_day - timedelta(days=days - 1)

    events: list[RawEvent] = []
    for day_offset in range(days):
        bucket = start_day + timedelta(days=day_offset)
        for _ in range(events_per_day):
            events.append(_build_event(bucket))

    db.add_all(events)
    db.commit()
    return len(events)


def inject_anomaly(db: Session, anomaly_type: str, amount: int | None = None) -> dict[str, Any]:
    seeded_count = _ensure_seed_data(db)

    if anomaly_type == "duplicate":
        result = _inject_duplicate_events(db, amount or DEFAULT_INJECTION_AMOUNT)
    elif anomaly_type == "missing_fields":
        result = _inject_missing_field_events(db, amount or DEFAULT_INJECTION_AMOUNT)
    elif anomaly_type == "invalid_values":
        result = _inject_invalid_value_events(db, amount or DEFAULT_INJECTION_AMOUNT)
    elif anomaly_type == "spike":
        result = _inject_spike_events(db, amount)
    elif anomaly_type == "drop":
        result = _inject_drop_events(db, amount)
    else:
        raise ValueError(f"Unsupported anomaly type: {anomaly_type}")

    result["seeded_event_count"] = seeded_count
    db.commit()
    return result


def _ensure_seed_data(db: Session) -> int:
    total_events = db.query(func.count(RawEvent.id)).scalar() or 0
    if total_events > 0:
        return 0

    return seed_events(db, days=DEFAULT_SEED_DAYS, events_per_day=DEFAULT_EVENTS_PER_DAY)


def _inject_duplicate_events(db: Session, amount: int) -> dict[str, Any]:
    source_events = (
        db.query(RawEvent)
        .order_by(RawEvent.time_bucket.desc(), RawEvent.id.desc())
        .limit(amount)
        .all()
    )
    if not source_events:
        raise RuntimeError("No source events available for duplicate injection.")

    duplicates = [
        _copy_event(source_event, anomaly_type="duplicate")
        for source_event in source_events
    ]
    db.add_all(duplicates)

    return {
        "anomaly_type": "duplicate",
        "target_bucket": source_events[0].time_bucket,
        "inserted_event_count": len(duplicates),
        "message": f"Inserted {len(duplicates)} duplicate events by reusing existing event_id values.",
    }


def _inject_missing_field_events(db: Session, amount: int) -> dict[str, Any]:
    target_bucket = _latest_bucket(db)
    events = [
        _build_event(target_bucket, anomaly_type="missing_fields", missing_fields=True)
        for _ in range(amount)
    ]
    db.add_all(events)

    return {
        "anomaly_type": "missing_fields",
        "target_bucket": target_bucket,
        "inserted_event_count": len(events),
        "message": f"Inserted {len(events)} events with missing required fields.",
    }


def _inject_invalid_value_events(db: Session, amount: int) -> dict[str, Any]:
    target_bucket = _latest_bucket(db)
    events = [
        _build_event(target_bucket, anomaly_type="invalid_values", invalid_values=True)
        for _ in range(amount)
    ]
    db.add_all(events)

    return {
        "anomaly_type": "invalid_values",
        "target_bucket": target_bucket,
        "inserted_event_count": len(events),
        "message": f"Inserted {len(events)} events with invalid enum values.",
    }


def _inject_spike_events(db: Session, amount: int | None) -> dict[str, Any]:
    target_bucket = _next_bucket(db)
    baseline = _average_daily_event_count(db)
    event_count = amount or max(baseline * 3, baseline + 50, 150)
    events = [_build_event(target_bucket, anomaly_type="spike") for _ in range(event_count)]
    db.add_all(events)

    return {
        "anomaly_type": "spike",
        "target_bucket": target_bucket,
        "inserted_event_count": len(events),
        "message": f"Inserted {len(events)} events in a new daily bucket to create an event count spike.",
    }


def _inject_drop_events(db: Session, amount: int | None) -> dict[str, Any]:
    target_bucket = _next_bucket(db)
    baseline = _average_daily_event_count(db)
    event_count = amount or max(1, baseline // 10)
    events = [_build_event(target_bucket, anomaly_type="drop") for _ in range(event_count)]
    db.add_all(events)

    return {
        "anomaly_type": "drop",
        "target_bucket": target_bucket,
        "inserted_event_count": len(events),
        "message": f"Inserted only {len(events)} events in a new daily bucket to create an event count drop.",
    }


def _build_event(
    bucket: date,
    anomaly_type: str | None = None,
    missing_fields: bool = False,
    invalid_values: bool = False,
) -> RawEvent:
    event_type = random.choice(VALID_EVENT_TYPES)
    device_type = random.choice(VALID_DEVICE_TYPES)
    user_id = f"user_{random.randint(1, 250):04d}"

    if missing_fields:
        user_id = None
        event_type = None

    if invalid_values:
        event_type = "unsupported_event"
        device_type = "unknown_device"

    return RawEvent(
        event_id=str(uuid.uuid4()),
        user_id=user_id,
        event_type=event_type,
        device_type=device_type,
        event_timestamp=_random_timestamp(bucket),
        time_bucket=bucket,
        payload=_build_payload(event_type),
        is_injected_anomaly=anomaly_type is not None,
        injected_anomaly_type=anomaly_type,
    )


def _copy_event(source_event: RawEvent, anomaly_type: str) -> RawEvent:
    return RawEvent(
        event_id=source_event.event_id,
        user_id=source_event.user_id,
        event_type=source_event.event_type,
        device_type=source_event.device_type,
        event_timestamp=source_event.event_timestamp,
        time_bucket=source_event.time_bucket,
        payload=dict(source_event.payload or {}),
        is_injected_anomaly=True,
        injected_anomaly_type=anomaly_type,
    )


def _build_payload(event_type: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": random.choice(["organic", "paid", "referral", "email"]),
        "campaign": random.choice(["spring", "summer", "academic_demo", "baseline"]),
    }
    if event_type == "purchase":
        payload["amount"] = round(random.uniform(10, 500), 2)
    return payload


def _random_timestamp(bucket: date) -> datetime:
    return datetime.combine(
        bucket,
        time(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        ),
        tzinfo=timezone.utc,
    )


def _latest_bucket(db: Session) -> date:
    latest = db.query(func.max(RawEvent.time_bucket)).scalar()
    if latest is None:
        return datetime.now(timezone.utc).date()
    return latest


def _next_bucket(db: Session) -> date:
    return _latest_bucket(db) + timedelta(days=1)


def _average_daily_event_count(db: Session) -> int:
    daily_counts = [
        count
        for _, count in db.query(RawEvent.time_bucket, func.count(RawEvent.id))
        .group_by(RawEvent.time_bucket)
        .all()
    ]
    if not daily_counts:
        return DEFAULT_EVENTS_PER_DAY
    return max(1, round(sum(daily_counts) / len(daily_counts)))
