import datetime
import json
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import (
    WearableConnection, WearableMetric, WearableSync, TimelineEvent,
)
from app.services.wearables.mock_provider import MockWearableProvider
from app.services.wearables.schemas import (
    DailyMetrics, DailyMetricItem, WearableInsight,
)

_PROVIDERS = {
    "fitbit_mock": MockWearableProvider,
}


def get_provider(provider_name: str):
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown wearable provider: {provider_name}")
    return cls()


def demo_connect(profile_id: str, db: Session) -> WearableConnection:
    existing = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.profile_id == profile_id,
            WearableConnection.provider == "fitbit_mock",
            WearableConnection.status == "connected",
        )
        .first()
    )
    if existing:
        return existing

    provider = get_provider("fitbit_mock")
    device = provider.get_device_info()
    now = datetime.datetime.utcnow()

    conn = WearableConnection(
        id=str(uuid4()),
        profile_id=profile_id,
        provider=device.provider,
        device_name=device.device_name,
        device_type=device.device_type,
        status="connected",
        connected_at=now,
        last_synced_at=now,
    )
    db.add(conn)
    db.flush()

    _store_metrics(conn.id, provider.get_daily_metrics().metrics, db)

    sync_entry = WearableSync(
        id=str(uuid4()),
        connection_id=conn.id,
        started_at=now,
        completed_at=now,
        status="success",
        records_synced=247,
    )
    db.add(sync_entry)
    db.commit()
    db.refresh(conn)
    return conn


def sync_device(connection_id: str, profile_id: str, db: Session) -> dict:
    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.id == connection_id,
            WearableConnection.profile_id == profile_id,
        )
        .first()
    )
    if conn is None:
        raise ValueError("Connection not found")
    if conn.status != "connected":
        raise ValueError("Device is not connected")

    provider = get_provider(conn.provider)
    now = datetime.datetime.utcnow()

    sync_entry = WearableSync(
        id=str(uuid4()),
        connection_id=conn.id,
        started_at=now,
        status="running",
    )
    db.add(sync_entry)
    db.flush()

    try:
        result = provider.sync()
        _store_metrics(conn.id, result.metrics, db)

        sync_entry.completed_at = datetime.datetime.utcnow()
        sync_entry.status = "success"
        sync_entry.records_synced = result.records_synced
        conn.last_synced_at = datetime.datetime.utcnow()

        steps_val = next((m.value for m in result.metrics if m.metric_type == "steps"), 0)
        sleep_val = next((m.value for m in result.metrics if m.metric_type == "sleep"), 0)
        cal_val = next((m.value for m in result.metrics if m.metric_type == "active_calories"), 0)

        tl = TimelineEvent(
            id=str(uuid4()),
            profile_id=profile_id,
            date=datetime.date.today().isoformat(),
            event_type="wearable",
            title=f"Wearable synced — {conn.device_name}",
            description=f"{int(steps_val)} steps \u2022 {sleep_val}h sleep \u2022 {int(cal_val)} kcal",
            is_ai_generated=False,
        )
        db.add(tl)

    except Exception as e:
        sync_entry.completed_at = datetime.datetime.utcnow()
        sync_entry.status = "failed"
        sync_entry.error_message = str(e)

    db.commit()
    db.refresh(sync_entry)
    return {
        "sync_id": sync_entry.id,
        "status": sync_entry.status,
        "records_synced": sync_entry.records_synced,
        "started_at": sync_entry.started_at.isoformat(),
        "completed_at": sync_entry.completed_at.isoformat() if sync_entry.completed_at else None,
        "error_message": sync_entry.error_message,
    }


def disconnect_device(connection_id: str, profile_id: str, db: Session) -> WearableConnection:
    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.id == connection_id,
            WearableConnection.profile_id == profile_id,
        )
        .first()
    )
    if conn is None:
        raise ValueError("Connection not found")
    conn.status = "disconnected"
    conn.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(conn)
    return conn


def get_today_metrics(connection_id: str, profile_id: str, db: Session) -> list[dict]:
    conn = _get_connection(connection_id, profile_id, db)
    metrics = (
        db.query(WearableMetric)
        .filter(WearableMetric.connection_id == conn.id)
        .order_by(desc(WearableMetric.recorded_at))
        .all()
    )
    seen: set[str] = set()
    result = []
    for m in metrics:
        if m.metric_type not in seen:
            seen.add(m.metric_type)
            result.append({
                "metric_type": m.metric_type,
                "value": m.value,
                "unit": m.unit,
                "source": m.source,
                "metadata": json.loads(m.metadata_json) if m.metadata_json else None,
            })
    return result


def get_weekly_steps(connection_id: str, profile_id: str, db: Session) -> list[dict]:
    conn = _get_connection(connection_id, profile_id, db)
    provider = get_provider(conn.provider)
    weekly = provider.get_weekly_metrics()
    if not weekly:
        return []
    return [{"day": d.day, "steps": d.steps} for d in weekly[0].days]


def get_sync_history(connection_id: str, profile_id: str, db: Session, limit: int = 10) -> list[dict]:
    conn = _get_connection(connection_id, profile_id, db)
    syncs = (
        db.query(WearableSync)
        .filter(WearableSync.connection_id == conn.id)
        .order_by(desc(WearableSync.started_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "status": s.status,
            "records_synced": s.records_synced,
            "started_at": s.started_at.isoformat(),
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "error_message": s.error_message,
        }
        for s in syncs
    ]


def get_connected_summary(profile_id: str, db: Session) -> dict | None:
    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.profile_id == profile_id,
            WearableConnection.status == "connected",
        )
        .first()
    )
    if conn is None:
        return None

    metrics = (
        db.query(WearableMetric)
        .filter(WearableMetric.connection_id == conn.id)
        .order_by(desc(WearableMetric.recorded_at))
        .all()
    )
    seen: set[str] = set()
    latest: dict[str, WearableMetric] = {}
    for m in metrics:
        if m.metric_type not in seen:
            seen.add(m.metric_type)
            latest[m.metric_type] = m

    steps = latest.get("steps")
    rhr = latest.get("resting_heart_rate")
    sleep = latest.get("sleep")
    calories = latest.get("active_calories")
    water = latest.get("water")
    distance = latest.get("distance")

    sleep_metadata = None
    if sleep and sleep.metadata_json:
        try:
            sleep_metadata = json.loads(sleep.metadata_json)
        except json.JSONDecodeError:
            sleep_metadata = None

    return {
        "connection_id": conn.id,
        "device_name": conn.device_name,
        "device_type": conn.device_type,
        "provider": conn.provider,
        "status": conn.status,
        "last_synced_at": conn.last_synced_at.isoformat(),
        "steps": int(steps.value) if steps else None,
        "resting_heart_rate": int(rhr.value) if rhr else None,
        "sleep_hours": sleep.value if sleep else None,
        "sleep_score": sleep_metadata.get("sub_text") if sleep_metadata else None,
        "active_calories": int(calories.value) if calories else None,
        "hydration_liters": water.value if water else None,
        "distance_km": distance.value if distance else None,
    }


def generate_wearable_insight(profile_id: str, db: Session) -> WearableInsight | None:
    summary = get_connected_summary(profile_id, db)
    if summary is None:
        return None

    sleep_h = summary.get("sleep_hours")
    steps = summary.get("steps")

    if sleep_h is not None and sleep_h < 7:
        return WearableInsight(
            title="Activity is improving, but sleep remains below target",
            observed=f"{sleep_h}h average sleep",
            context="Your profile target is 7h",
            suggested_action="Aim for an additional 30\u201345 minutes of sleep tonight.",
        )

    if steps is not None and steps < 5000:
        return WearableInsight(
            title="Activity levels are below typical range",
            observed=f"{steps:,} steps today",
            context="General guidelines suggest 7,000\u201310,000 steps for adults",
            suggested_action="Consider a short walk after meals to increase daily activity.",
        )

    return WearableInsight(
        title="Wearable data looks consistent",
        observed=f"{summary.get('steps', 0):,} steps, {summary.get('resting_heart_rate', '—')} bpm resting HR",
        context="Data is within expected ranges for your profile",
        suggested_action="Keep up your current routine and stay hydrated.",
    )


def _get_connection(connection_id: str, profile_id: str, db: Session) -> WearableConnection:
    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.id == connection_id,
            WearableConnection.profile_id == profile_id,
        )
        .first()
    )
    if conn is None:
        raise ValueError("Connection not found")
    return conn


def _store_metrics(connection_id: str, items: list[DailyMetricItem], db: Session) -> None:
    now = datetime.datetime.utcnow()
    for item in items:
        metadata = None
        if item.target is not None or item.sub_text:
            metadata = json.dumps({"target": item.target, "sub_text": item.sub_text})
        metric = WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type=item.metric_type,
            value=item.value,
            unit=item.unit,
            recorded_at=now,
            source="mock",
            metadata_json=metadata,
        )
        db.add(metric)
