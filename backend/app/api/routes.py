from fastapi import APIRouter, Body, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, EvaluationResult, MetricSnapshot, RawEvent
from app.schemas import (
    AlertResponse,
    AnalyzeResponse,
    EvaluationResponse,
    HealthResponse,
    InjectAnomalyRequest,
    InjectAnomalyResponse,
    MetricSnapshotResponse,
    ResetResponse,
    SeedRequest,
    SeedResponse,
    SummaryResponse,
)
from app.services.anomaly_detection import detect_and_store_alerts
from app.services.evaluation import calculate_and_store_evaluation
from app.services.quality_metrics import calculate_and_store_metric_snapshots, latest_metric_values
from app.services.synthetic_events import inject_anomaly, seed_events

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", service="event-quality-dashboard-api")


@router.post("/seed", response_model=SeedResponse)
def seed_event_data(
    request: SeedRequest = Body(default=SeedRequest()),
    db: Session = Depends(get_db),
):
    inserted_count = seed_events(db, days=request.days, events_per_day=request.events_per_day)
    return SeedResponse(
        inserted_event_count=inserted_count,
        days=request.days,
        events_per_day=request.events_per_day,
    )


@router.post("/anomalies/inject", response_model=InjectAnomalyResponse)
def inject_controlled_anomaly(
    request: InjectAnomalyRequest,
    db: Session = Depends(get_db),
):
    result = inject_anomaly(db, anomaly_type=request.anomaly_type, amount=request.amount)
    return InjectAnomalyResponse(**result)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_event_data(db: Session = Depends(get_db)):
    db.query(Alert).delete()
    snapshots = calculate_and_store_metric_snapshots(db)
    alerts = detect_and_store_alerts(db, snapshots)
    evaluation = calculate_and_store_evaluation(db)
    latest_metrics = latest_metric_values(snapshots)
    db.commit()

    return AnalyzeResponse(
        metric_snapshot_count=len(snapshots),
        generated_alert_count=len(alerts),
        latest_metrics=latest_metrics,
        evaluation=EvaluationResponse(
            detection_rate=evaluation.detection_rate,
            false_alarm_rate=evaluation.false_alarm_rate,
            injected_anomaly_count=evaluation.injected_anomaly_count,
            detected_anomaly_count=evaluation.detected_anomaly_count,
            false_alarm_count=evaluation.false_alarm_count,
            total_alert_count=evaluation.total_alert_count,
        ),
    )


@router.post("/reset", response_model=ResetResponse)
def reset_demo_data(db: Session = Depends(get_db)):
    deleted_alerts = db.query(Alert).delete()
    deleted_metric_snapshots = db.query(MetricSnapshot).delete()
    deleted_evaluation_results = db.query(EvaluationResult).delete()
    deleted_raw_events = db.query(RawEvent).delete()
    db.commit()

    return ResetResponse(
        deleted_raw_events=deleted_raw_events,
        deleted_metric_snapshots=deleted_metric_snapshots,
        deleted_alerts=deleted_alerts,
        deleted_evaluation_results=deleted_evaluation_results,
        message="Demo data reset completed.",
    )


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    total_events = db.query(func.count(RawEvent.id)).scalar() or 0
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    latest_bucket = db.query(func.max(MetricSnapshot.time_bucket)).scalar()

    metric_values = {}
    if latest_bucket is not None:
        latest_snapshots = db.query(MetricSnapshot).filter(MetricSnapshot.time_bucket == latest_bucket).all()
        metric_values = {snapshot.metric_name: snapshot.value for snapshot in latest_snapshots}

    latest_alerts = (
        db.query(Alert)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(5)
        .all()
    )

    return SummaryResponse(
        total_events=total_events,
        total_alerts=total_alerts,
        missing_field_ratio=metric_values.get("missing_field_ratio", 0.0),
        duplicate_ratio=metric_values.get("duplicate_ratio", 0.0),
        invalid_value_count=int(metric_values.get("invalid_value_count", 0.0)),
        latest_event_count=int(metric_values.get("event_count", 0.0)),
        latest_alerts=latest_alerts,
    )


@router.get("/metrics", response_model=list[MetricSnapshotResponse])
def get_metrics(db: Session = Depends(get_db)):
    return (
        db.query(MetricSnapshot)
        .order_by(MetricSnapshot.time_bucket.asc(), MetricSnapshot.metric_name.asc())
        .all()
    )


@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc(), Alert.id.desc()).all()


@router.get("/evaluation", response_model=EvaluationResponse)
def get_evaluation(db: Session = Depends(get_db)):
    evaluation = db.query(EvaluationResult).order_by(EvaluationResult.created_at.desc(), EvaluationResult.id.desc()).first()
    if evaluation is None:
        return EvaluationResponse(
            detection_rate=None,
            false_alarm_rate=None,
            injected_anomaly_count=0,
            detected_anomaly_count=0,
            false_alarm_count=0,
            total_alert_count=0,
        )

    return EvaluationResponse(
        detection_rate=evaluation.detection_rate,
        false_alarm_rate=evaluation.false_alarm_rate,
        injected_anomaly_count=evaluation.injected_anomaly_count,
        detected_anomaly_count=evaluation.detected_anomaly_count,
        false_alarm_count=evaluation.false_alarm_count,
        total_alert_count=evaluation.total_alert_count,
    )
