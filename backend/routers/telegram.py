import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db, settings
from ..models import TelegramCode, User
from ..security import current_user
from ..services.telegram_service import send_message

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/connect")
def connect(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not settings.telegram_bot_token: raise HTTPException(503, "Configure TELEGRAM_BOT_TOKEN no servidor")
    code = secrets.token_hex(3).upper()
    db.add(TelegramCode(user_id=user.id, code=code, expires_at=datetime.now() + timedelta(minutes=15)))
    db.commit(); return {"code": code, "expires_in_minutes": 15, "instruction": f"Envie {code} ao bot no Telegram."}


@router.delete("/connect")
def disconnect(user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.telegram_chat_id = None; db.commit(); return {"connected": False}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json(); message = data.get("message") or {}; text = (message.get("text") or "").strip().upper()
    chat_id = str((message.get("chat") or {}).get("id", ""))
    code = db.scalar(select(TelegramCode).where(TelegramCode.code == text, TelegramCode.used.is_(False), TelegramCode.expires_at > datetime.now()))
    if code and chat_id:
        user = db.get(User, code.user_id); user.telegram_chat_id = chat_id; code.used = True; db.commit()
        await send_message(chat_id, "✅ Telegram conectado ao MedTrack. Você poderá receber lembretes configurados.")
    return {"ok": True}

