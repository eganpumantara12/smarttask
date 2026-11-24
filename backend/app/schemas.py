from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Status = Literal["todo", "doing", "done"]


def to_utc(v: datetime | None) -> datetime | None:
    """Deadline selalu dinormalkan ke UTC; waktu tanpa zona dianggap UTC."""
    if v is None:
        return None
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v.astimezone(timezone.utc)


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nama minimal 2 karakter.")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CourseIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    color: str = Field(default="#2563eb", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nama mata kuliah wajib diisi.")
        return v


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: str
    task_count: int = 0
    open_task_count: int = 0


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course_id: int
    description: str = Field(default="", max_length=2000)
    deadline: datetime

    @field_validator("deadline")
    @classmethod
    def deadline_utc(cls, v: datetime) -> datetime:
        return to_utc(v)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nama tugas wajib diisi.")
        return v


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    course_id: int | None = None
    description: str | None = Field(default=None, max_length=2000)
    deadline: datetime | None = None
    status: Status | None = None

    @field_validator("deadline")
    @classmethod
    def deadline_utc(cls, v: datetime | None) -> datetime | None:
        return to_utc(v)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Nama tugas wajib diisi.")
        return v


class StatusIn(BaseModel):
    status: Status


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    deadline: datetime
    status: Status
    course_id: int
    course_name: str
    course_color: str
    is_overdue: bool  # lewat deadline dan belum selesai
    is_due_soon: bool  # mendekati deadline dan belum selesai
    created_at: datetime
    updated_at: datetime


class AdminUserPatch(BaseModel):
    is_active: bool


class ResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)


class SettingsIn(BaseModel):
    reminder_enabled: bool
    reminder_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM, waktu lokal perangkat
    reminder_sound: bool
    deadline_alert_hours: Literal[0, 1, 3, 6, 12, 24]  # 0 = tanpa peringatan sebelum deadline


class SettingsOut(SettingsIn):
    model_config = ConfigDict(from_attributes=True)


class AdminUserOut(BaseModel):
    """Data pemantauan akun. Sengaja hanya berisi jumlah, tidak berisi judul atau isi tugas."""

    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    course_count: int
    task_count: int
    open_task_count: int


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    new_last_7_days: int
    active_last_24h: int
    total_courses: int
    total_tasks: int
    done_tasks: int
