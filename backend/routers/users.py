from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import Login, UserCreate
from ..security import current_user, hash_password, token_for, verify_password

router = APIRouter(prefix="/api", tags=["usuários"])


@router.post("/users", status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Este e-mail já está cadastrado")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": token_for(user), "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.post("/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "E-mail ou senha incorretos")
    return {"token": token_for(user), "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "telegram_connected": bool(user.telegram_chat_id), "daily_summary": user.daily_summary}

