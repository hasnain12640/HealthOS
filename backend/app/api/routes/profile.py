import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_profile
from app.models.models import User, HealthProfile

router = APIRouter()


class ProfileCreate(BaseModel):
    user_name: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    blood_group: str
    city: str
    language: str = "en"


class ProfileResponse(BaseModel):
    id: str
    user_name: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    blood_group: str
    city: str
    language: str

    class Config:
        from_attributes = True


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists")

    profile = HealthProfile(id=str(uuid.uuid4()), user_id=user.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=ProfileResponse)
def get_profile(profile: HealthProfile = Depends(get_current_profile)):
    return profile
