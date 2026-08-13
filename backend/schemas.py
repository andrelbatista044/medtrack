from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    email: EmailStr
    password: str


class MedicationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dosage: str = Field(min_length=1, max_length=80)
    times: list[str] = Field(min_length=1, max_length=12)
    frequency: str = Field(default="Todos os dias", max_length=80)
    start_date: date
    end_date: date | None = None
    quantity: int = Field(default=0, ge=0, le=100000)
    notes: str = Field(default="", max_length=1000)
    active: bool = True

    @field_validator("times")
    @classmethod
    def valid_times(cls, values):
        for value in values:
            parts = value.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts) or not 0 <= int(parts[0]) <= 23 or not 0 <= int(parts[1]) <= 59:
                raise ValueError("Horário inválido; use HH:MM")
        return sorted(set(values))


class CaregiverIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=3, max_length=255)
    telegram_chat_id: str | None = Field(default=None, max_length=64)
    alerts_enabled: bool = True


class SnoozeIn(BaseModel):
    minutes: int = Field(default=10, ge=5, le=120)

