import json, os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

# Permite executar tanto `python backend/main.py` quanto
# `uvicorn backend.main:app --reload` mantendo imports de pacote consistentes.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "backend"

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base, SessionLocal, engine, get_db, settings
from .models import Caregiver, Dose, Medication, User
from .routers import caregiver, doses, medications, telegram, users
from .security import current_user
from .services.medication_service import ensure_doses
from .services.notification_service import process_due_notifications

BASE = Path(__file__).resolve().parent.parent
FRONTEND = BASE / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MedTrack API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.app_base_url, "http://localhost:8000", "http://127.0.0.1:8000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for router in (users.router, medications.router, doses.router, telegram.router, caregiver.router): app.include_router(router)


@app.get("/api/health")
def health(): return {"status": "ok", "database": settings.database_url.split(":", 1)[0], "telegram_configured": bool(settings.telegram_bot_token)}


@app.post("/api/demo", status_code=201)
def demo(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(Medication.id).where(Medication.user_id == user.id)):
        raise HTTPException(409, "Sua conta já possui medicamentos")
    meds = [Medication(user_id=user.id, name="Vitamina D", dosage="1 cápsula", times_json='["08:00"]', frequency="Todos os dias", start_date=date.today()-timedelta(days=10), quantity=24, notes="Dados de demonstração"),
            Medication(user_id=user.id, name="Medicamento demonstrativo", dosage="500 mg", times_json='["14:00", "20:00"]', frequency="Todos os dias", start_date=date.today()-timedelta(days=10), quantity=18, notes="Exemplo fictício — não é orientação médica")]
    db.add_all(meds); db.commit(); ensure_doses(db, user.id, date.today()-timedelta(days=7), 8)
    past = db.scalars(select(Dose).where(Dose.user_id == user.id, Dose.scheduled_at < datetime.now()).order_by(Dose.scheduled_at)).all()
    for index, dose in enumerate(past):
        dose.status = "TAKEN" if index % 6 not in (4, 5) else ("LATE" if index % 6 == 4 else "MISSED")
        if dose.status != "MISSED": dose.confirmed_at = dose.scheduled_at + timedelta(minutes=5 if dose.status == "TAKEN" else 45)
    db.commit(); return {"created": True, "notice": "Dados fictícios de demonstração carregados."}


@app.post("/api/cron/notifications")
async def cron_notifications(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    if settings.cron_secret and authorization != f"Bearer {settings.cron_secret}": raise HTTPException(401, "Não autorizado")
    return await process_due_notifications(db)


app.mount("/css", StaticFiles(directory=FRONTEND / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND / "js"), name="js")


@app.get("/")
def index(): return FileResponse(FRONTEND / "index.html")


@app.get("/{page}.html")
def page(page: str):
    target = FRONTEND / f"{page}.html"
    return FileResponse(target) if target.is_file() else FileResponse(FRONTEND / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
