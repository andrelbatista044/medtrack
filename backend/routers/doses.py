from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Dose, Medication, User
from ..schemas import SnoozeIn
from ..security import current_user
from ..services.medication_service import dose_dict, ensure_doses, refresh_late_statuses
from ..time_utils import local_now, local_today

router = APIRouter(prefix="/api", tags=["doses"])


def owned_dose(db: Session, dose_id: int, user_id: int) -> Dose:
    dose = db.scalar(select(Dose).where(Dose.id == dose_id, Dose.user_id == user_id))
    if not dose: raise HTTPException(404, "Dose não encontrada")
    return dose


@router.get("/doses")
def doses(day: date | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    day = day or local_today(); ensure_doses(db, user.id, day, 1); refresh_late_statuses(db, user.id)
    items = db.scalars(select(Dose).where(Dose.user_id == user.id, Dose.scheduled_at >= datetime.combine(day, time.min),
                                          Dose.scheduled_at <= datetime.combine(day, time.max)).order_by(Dose.scheduled_at)).all()
    return [dose_dict(x) for x in items]


@router.post("/doses/{dose_id}/{status}")
def change_status(dose_id: int, status: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    mapping = {"taken": "TAKEN", "late": "LATE", "missed": "MISSED", "skipped": "SKIPPED"}
    if status not in mapping: raise HTTPException(422, "Status inválido")
    dose = owned_dose(db, dose_id, user.id); dose.status = mapping[status]
    dose.confirmed_at = local_now() if status in ("taken", "late") else None
    if status == "taken" and dose.confirmed_at > dose.scheduled_at + timedelta(minutes=30): dose.status = "LATE"
    if dose.status in ("TAKEN", "LATE") and dose.medication.quantity > 0: dose.medication.quantity -= 1
    db.commit(); return dose_dict(dose)


@router.post("/doses/{dose_id}/snooze")
def snooze(dose_id: int, data: SnoozeIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dose = owned_dose(db, dose_id, user.id); dose.snoozed_until = local_now() + timedelta(minutes=data.minutes)
    dose.notification_sent_at = None; db.commit(); return dose_dict(dose)


@router.get("/history")
def history(start: date | None = None, end: date | None = None, medication_id: int | None = None,
            status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Dose).where(Dose.user_id == user.id)
    if start: query = query.where(Dose.scheduled_at >= datetime.combine(start, time.min))
    if end: query = query.where(Dose.scheduled_at <= datetime.combine(end, time.max))
    if medication_id: query = query.where(Dose.medication_id == medication_id)
    if status: query = query.where(Dose.status == status.upper())
    return [dose_dict(x) for x in db.scalars(query.order_by(Dose.scheduled_at.desc()).limit(500)).all()]


@router.get("/adherence")
def adherence(days: int = Query(30, ge=1, le=365), user: User = Depends(current_user), db: Session = Depends(get_db)):
    now = local_now(); since = now - timedelta(days=days)
    items = db.scalars(select(Dose).where(Dose.user_id == user.id, Dose.scheduled_at >= since, Dose.scheduled_at <= now)).all()
    counts = {key: 0 for key in ("TAKEN", "LATE", "MISSED", "SKIPPED", "PENDING")}
    daily = {}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
        key = item.scheduled_at.date().isoformat(); daily.setdefault(key, [0, 0])
        daily[key][1] += 1
        if item.status in ("TAKEN", "LATE"): daily[key][0] += 1
    considered = sum(counts[x] for x in ("TAKEN", "LATE", "MISSED", "SKIPPED"))
    percentage = round((counts["TAKEN"] + counts["LATE"]) * 100 / considered) if considered else 0
    evolution = [{"date": key, "percentage": round(ok * 100 / total)} for key, (ok, total) in sorted(daily.items())]
    return {"percentage": percentage, "counts": counts, "evolution": evolution, "disclaimer": "Indicador de organização da rotina; não é uma avaliação médica."}


@router.get("/insights")
def insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    since = local_now() - timedelta(days=30)
    items = db.scalars(select(Dose).where(Dose.user_id == user.id, Dose.scheduled_at >= since, Dose.status.in_(["LATE", "MISSED"]))).all()
    if not items: return {"insights": ["Ainda não há registros suficientes para identificar padrões na rotina."]}
    hours = {}; meds = {}; weekdays = {}
    for dose in items:
        hours[dose.scheduled_at.hour] = hours.get(dose.scheduled_at.hour, 0) + 1
        meds[dose.medication.name] = meds.get(dose.medication.name, 0) + 1
        weekdays[dose.scheduled_at.strftime("%A")] = weekdays.get(dose.scheduled_at.strftime("%A"), 0) + 1
    hour = max(hours, key=hours.get); med = max(meds, key=meds.get)
    return {"insights": [f"O horário das {hour:02d}:00 concentrou mais atrasos ou esquecimentos nos últimos 30 dias.",
                           f"{med} foi o medicamento com mais registros de atraso ou esquecimento no período."],
            "disclaimer": "Análise exclusiva dos registros; não altera nem recomenda tratamento."}
