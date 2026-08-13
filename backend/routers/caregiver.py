from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Caregiver, User
from ..schemas import CaregiverIn
from ..security import current_user

router = APIRouter(prefix="/api/caregiver", tags=["cuidador"])


def payload(x):
    return {"id": x.id, "name": x.name, "contact": x.contact, "telegram_chat_id": x.telegram_chat_id,
            "alerts_enabled": x.alerts_enabled, "can_edit": False}


@router.get("")
def list_caregivers(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [payload(x) for x in db.scalars(select(Caregiver).where(Caregiver.user_id == user.id)).all()]


@router.post("", status_code=201)
def create_caregiver(data: CaregiverIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Caregiver(user_id=user.id, **data.model_dump(), can_edit=False); db.add(item); db.commit(); db.refresh(item)
    return payload(item)


@router.delete("/{item_id}", status_code=204)
def delete_caregiver(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Caregiver).where(Caregiver.id == item_id, Caregiver.user_id == user.id))
    if item: db.delete(item); db.commit()

