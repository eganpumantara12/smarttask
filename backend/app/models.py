from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, UTCDateTime, utcnow

STATUSES = ("todo", "doing", "done")  # belum dikerjakan, sedang dikerjakan, selesai


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")  # student | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    # Pengaturan pengingat milik pengguna (tersimpan di server agar sama di HP dan laptop)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    reminder_time: Mapped[str] = mapped_column(String(5), default="08:00", server_default="08:00")
    reminder_sound: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    deadline_alert_hours: Mapped[int] = mapped_column(Integer, default=3, server_default="3")  # 0 = mati
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)

class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_course_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(9), default="#2563eb")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    # Indeks pada deadline agar pengurutan tetap cepat (NFR-02)
    __table_args__ = (Index("ix_tasks_user_deadline", "user_id", "deadline"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(20), default="todo")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    course: Mapped[Course] = relationship(back_populates="tasks")
    email_reminded = Column(Boolean, default=False, nullable=False)
