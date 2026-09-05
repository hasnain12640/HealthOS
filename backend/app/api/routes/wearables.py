from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_profile
from app.models.models import HealthProfile, WearableConnection
from app.services.wearables import service

router = APIRouter()


@router.get("")
def list_devices(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    connections = (
        db.query(WearableConnection)
        .filter(WearableConnection.profile_id == profile.id)
        .order_by(WearableConnection.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "device_name": c.device_name,
            "device_type": c.device_type,
            "status": c.status,
            "connected_at": c.connected_at.isoformat(),
            "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
        }
        for c in connections
    ]


@router.get("/status")
def integration_status(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    summary = service.get_connected_summary(profile.id, db)
    insight = service.generate_wearable_insight(profile.id, db)
    return {
        "connected": summary is not None,
        "device": summary,
        "insight": insight.model_dump() if insight else None,
    }


@router.post("/demo/connect")
def demo_connect(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    conn = service.demo_connect(profile.id, db)
    return {
        "id": conn.id,
        "provider": conn.provider,
        "device_name": conn.device_name,
        "device_type": conn.device_type,
        "status": conn.status,
        "connected_at": conn.connected_at.isoformat(),
        "last_synced_at": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
    }


@router.get("/{connection_id}")
def get_device(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.id == connection_id,
            WearableConnection.profile_id == profile.id,
        )
        .first()
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="Wearable connection not found")
    return {
        "id": conn.id,
        "provider": conn.provider,
        "device_name": conn.device_name,
        "device_type": conn.device_type,
        "status": conn.status,
        "connected_at": conn.connected_at.isoformat(),
        "last_synced_at": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
    }


@router.get("/{connection_id}/metrics/today")
def today_metrics(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    try:
        return service.get_today_metrics(connection_id, profile.id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{connection_id}/metrics/weekly")
def weekly_metrics(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    try:
        return service.get_weekly_steps(connection_id, profile.id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{connection_id}/syncs")
def sync_history(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    try:
        return service.get_sync_history(connection_id, profile.id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{connection_id}/sync")
def sync_device(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    try:
        return service.sync_device(connection_id, profile.id, db)
    except ValueError as e:
        code = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=code, detail=str(e))


@router.post("/{connection_id}/disconnect")
def disconnect_device(
    connection_id: str,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    try:
        conn = service.disconnect_device(connection_id, profile.id, db)
        return {
            "id": conn.id,
            "status": conn.status,
            "device_name": conn.device_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
