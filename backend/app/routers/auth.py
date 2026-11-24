import logging
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.services.email_service import send_verification_otp

from ..database import get_db, utcnow
from ..deps import get_current_user
from ..logging_conf import log_event
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = logging.getLogger("smarttask.auth")

# Hash palsu agar waktu respons login tidak membocorkan apakah email terdaftar.
_DUMMY_HASH = hash_password("dummy-password")


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email sudah terdaftar.")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password), role="student")
    db.add(user)
    db.commit()
    log_event(log, "register", user_id=user.id, result="ok")
    return TokenOut(access_token=create_access_token(user.id, user.role), user=user)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    ok = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok:
        log_event(log, "login", result="gagal")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email atau password salah.")
    if not user.is_active:
        log_event(log, "login", user_id=user.id, result="akun_nonaktif")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Akun Anda dinonaktifkan. Hubungi admin.")
    user.last_login_at = utcnow()
    db.commit()
    log_event(log, "login", user_id=user.id, result="ok")
    return TokenOut(access_token=create_access_token(user.id, user.role), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user)):
    # Token bersifat stateless dan berumur pendek; klien membuang token. Server hanya mencatat log.
    log_event(log, "logout", user_id=user.id, result="ok")
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp_code: str


def _generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Akun tidak ditemukan.")

    if getattr(user, "is_verified", False):
        return {"message": "Email sudah terverifikasi. Silakan login."}

    now = datetime.now(timezone.utc)
    expires = user.otp_expires_at
    if expires is not None and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if not user.otp_code or user.otp_code != payload.otp_code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kode OTP salah.")

    if expires is not None and expires < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode OTP sudah kedaluwarsa. Silakan daftar ulang untuk mengirim OTP baru.",
        )

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()

    return {"message": "Verifikasi email berhasil. Akun Anda sekarang aktif."}
