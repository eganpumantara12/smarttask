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


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()

    # 1. Kalau email sudah terdaftar DAN sudah diverifikasi, tolak
    if existing_user and getattr(existing_user, "is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar dan aktif."
        )

    # 2. Siapkan kode OTP 6 digit & waktu kedaluwarsa 15 menit
    otp_code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    if existing_user:
        # Kalau pernah daftar tapi dulu belum sempat verifikasi OTP, perbarui datanya
        existing_user.password_hash = hash_password(payload.password)
        existing_user.otp_code = otp_code
        existing_user.otp_expires_at = expires_at
        # (Jika di form daftarmu ada field nama, update juga existing_user.name = payload.name)
    else:
        # Buat user baru dengan status belum terverifikasi
        new_user = User(
            email=email_clean,
            password_hash=hash_password(payload.password),
            is_verified=False,
            otp_code=otp_code,
            otp_expires_at=expires_at,
            # (Tambahkan field lain seperti name=payload.name jika ada di model User kamu)
        )
        db.add(new_user)

    db.commit()

    # 3. Kirim kode OTP ke email pendaftar
    sent = send_verification_otp(email_clean, otp_code)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal mengirim email OTP. Cek pengaturan SMTP di Railway."
        )

    return {
        "message": "Pendaftaran berhasil. Kode OTP telah dikirim ke email Anda.",
        "email": email_clean
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    # 1. Cek kecocokan email & password seperti biasa
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah."
        )

    # 2. TAMBAHAN BARU: Cek apakah email sudah diverifikasi OTP
    if not getattr(user, "is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email belum diverifikasi. Silakan masukkan kode OTP dari email Anda."
        )

    # 3. Buat dan kembalikan token login seperti kode aslimu
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


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
