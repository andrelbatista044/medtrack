import json
from datetime import date, datetime, time, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Dose, Medication
from ..time_utils import local_now, local_today


def medication_dict(item: Medication) -> dict:
    return {"id": item.id, "name": item.name, "dosage": item.dosage, "times": json.loads(item.times_json),
            "frequency": item.frequency, "start_date": item.start_date.isoformat(),
            "end_date": item.end_date.isoformat() if item.end_date else None, "quantity": item.quantity,
            "notes": item.notes, "active": item.active}


def dose_dict(item: Dose) -> dict:
    return {"id": item.id, "medication_id": item.medication_id, "medication": item.medication.name,
            "dosage": item.medication.dosage, "scheduled_at": item.scheduled_at.isoformat(),
            "confirmed_at": item.confirmed_at.isoformat() if item.confirmed_at else None,
            "snoozed_until": item.snoozed_until.isoformat() if item.snoozed_until else None, "status": item.status}


def ensure_doses(db: Session, user_id: int, start: date | None = None, days: int = 7) -> int:
    start = start or local_today()
    meds = db.scalars(select(Medication).where(Medication.user_id == user_id, Medication.active.is_(True))).all()
    created = 0
    for medication in meds:
        for offset in range(days):
            day = start + timedelta(days=offset)
            if day < medication.start_date or (medication.end_date and day > medication.end_date):
                continue
            for raw in json.loads(medication.times_json):
                hour, minute = map(int, raw.split(":"))
                scheduled = datetime.combine(day, time(hour, minute))
                exists = db.scalar(select(Dose.id).where(Dose.medication_id == medication.id, Dose.scheduled_at == scheduled))
                if not exists:
                    db.add(Dose(user_id=user_id, medication_id=medication.id, scheduled_at=scheduled))
                    created += 1
    db.commit()
    return created


def refresh_late_statuses(db: Session, user_id: int) -> None:
    cutoff = local_now() - timedelta(minutes=30)
    doses = db.scalars(select(Dose).where(Dose.user_id == user_id, Dose.status == "PENDING", Dose.scheduled_at < cutoff)).all()
    for dose in doses:
        dose.status = "LATE"
    db.commit()
