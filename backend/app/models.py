from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    time_bucket: Mapped[date] = mapped_column(Date, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_injected_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    injected_anomaly_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[float] = mapped_column(Float)
    time_bucket: Mapped[date] = mapped_column(Date, index=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    detection_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True)
    anomaly_type: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    time_bucket: Mapped[date] = mapped_column(Date, index=True)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    detection_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    false_alarm_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    injected_anomaly_count: Mapped[int] = mapped_column(Integer, default=0)
    detected_anomaly_count: Mapped[int] = mapped_column(Integer, default=0)
    false_alarm_count: Mapped[int] = mapped_column(Integer, default=0)
    total_alert_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
