from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class SeedRequest(BaseModel):
    days: int = Field(default=14, ge=1, le=90)
    events_per_day: int = Field(default=100, ge=1, le=10000)


class SeedResponse(BaseModel):
    inserted_event_count: int
    days: int
    events_per_day: int


class InjectAnomalyRequest(BaseModel):
    anomaly_type: Literal["duplicate", "missing_fields", "invalid_values", "spike", "drop"]
    amount: int | None = Field(default=None, ge=1, le=10000)


class InjectAnomalyResponse(BaseModel):
    anomaly_type: str
    target_bucket: date
    inserted_event_count: int
    seeded_event_count: int = 0
    message: str


class MetricSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric_name: str
    value: float
    time_bucket: date
    is_anomaly: bool
    detection_method: str | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric_name: str
    anomaly_type: str
    severity: str
    time_bucket: date
    reason: str
    created_at: datetime | None = None


class EvaluationResponse(BaseModel):
    detection_rate: float | None
    false_alarm_rate: float | None
    injected_anomaly_count: int
    detected_anomaly_count: int
    false_alarm_count: int
    total_alert_count: int


class AnalyzeResponse(BaseModel):
    metric_snapshot_count: int
    generated_alert_count: int
    latest_metrics: dict[str, float]
    evaluation: EvaluationResponse


class ResetResponse(BaseModel):
    deleted_raw_events: int
    deleted_metric_snapshots: int
    deleted_alerts: int
    deleted_evaluation_results: int
    message: str


class SummaryResponse(BaseModel):
    total_events: int
    total_alerts: int
    missing_field_ratio: float
    duplicate_ratio: float
    invalid_value_count: int
    latest_event_count: int
    latest_alerts: list[AlertResponse]
