from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Caregiver, Dose, User
from .telegram_service import send_message


async def process_due_notifications(db: Session) -> dict:
    now = datetime.now()
    window = now + timedelta(minutes=5)
    doses = db.scalars(select(Dose).where(Dose.status.in_(["PENDING", "LATE"]), Dose.notification_sent_at.is_(None), Dose.scheduled_at <= window)).all()
    sent = 0
    for dose in doses:
        user = db.get(User, dose.user_id)
        if user and user.telegram_chat_id:
            text = f"💊 Hora do medicamento!\n\nMedicamento: {dose.medication.name}\nDosagem: {dose.medication.dosage}\nHorário: {dose.scheduled_at:%H:%M}\n\nVocê já tomou?"
            markup = {"inline_keyboard": [[{"text": "✅ Tomei", "url": f"{__import__('backend.database', fromlist=['settings']).settings.app_base_url}/dashboard.html?dose={dose.id}"}]]}
            if await send_message(user.telegram_chat_id, text, markup):
                dose.notification_sent_at = now
                sent += 1
        if dose.scheduled_at < now - timedelta(minutes=30):
            dose.status = "LATE"
            caregivers = db.scalars(select(Caregiver).where(Caregiver.user_id == dose.user_id, Caregiver.alerts_enabled.is_(True))).all()
            for caregiver in caregivers:
                if caregiver.telegram_chat_id:
                    await send_message(caregiver.telegram_chat_id, f"🔴 Uma dose de {dose.medication.name} está atrasada e ainda não foi confirmada.")
    db.commit()
    return {"processed": len(doses), "sent": sent}

