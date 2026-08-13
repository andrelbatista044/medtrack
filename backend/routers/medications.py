import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Medication, User
from ..schemas import MedicationIn
from ..security import current_user
from ..services.medication_service import medication_dict

router = APIRouter(prefix="/api/medications", tags=["medicamentos"])


@router.get("")
def list_medications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [medication_dict(x) for x in db.scalars(select(Medication).where(Medication.user_id == user.id).order_by(Medication.name)).all()]


@router.post("", status_code=201)
def create_medication(data: MedicationIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.end_date and data.end_date < data.start_date:
        raise HTTPException(422, "A data final deve ser posterior à inicial")
    item = Medication(user_id=user.id, name=data.name.strip(), dosage=data.dosage.strip(), times_json=json.dumps(data.times),
                      frequency=data.frequency, start_date=data.start_date, end_date=data.end_date, quantity=data.quantity,
                      notes=data.notes.strip(), active=data.active)
    db.add(item); db.commit(); db.refresh(item)
    return medication_dict(item)


@router.put("/{item_id}")
def update_medication(item_id: int, data: MedicationIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Medication).where(Medication.id == item_id, Medication.user_id == user.id))
    if not item: raise HTTPException(404, "Medicamento não encontrado")
    for key in ("name", "dosage", "frequency", "start_date", "end_date", "quantity", "notes", "active"):
        setattr(item, key, getattr(data, key))
    item.times_json = json.dumps(data.times)
    db.commit(); return medication_dict(item)


@router.delete("/{item_id}", status_code=204)
def delete_medication(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Medication).where(Medication.id == item_id, Medication.user_id == user.id))
    if not item: raise HTTPException(404, "Medicamento não encontrado")
    db.delete(item); db.commit()

