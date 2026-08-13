from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    daily_summary: Mapped[bool] = mapped_column(Boolean, default=False)
    medications: Mapped[list["Medication"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    dosage: Mapped[str] = mapped_column(String(80))
    times_json: Mapped[str] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(String(80), default="Todos os dias")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped[User] = relationship(back_populates="medications")
    doses: Mapped[list["Dose"]] = relationship(back_populates="medication", cascade="all, delete-orphan")


class Dose(Base):
    __tablename__ = "doses"
    __table_args__ = (UniqueConstraint("medication_id", "scheduled_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    medication: Mapped[Medication] = relationship(back_populates="doses")


class Caregiver(Base):
    __tablename__ = "caregivers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str] = mapped_column(String(255))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)


class TelegramCode(Base):
    __tablename__ = "telegram_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

