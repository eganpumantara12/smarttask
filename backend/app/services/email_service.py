import logging
import os
import smtplib
import socket
from email.message import EmailMessage

log = logging.getLogger("app.services.email_service")


def _get_smtp_config() -> tuple[str, int, str, str, str] | None:
    host = os.getenv("SMTP_HOST", "").strip()
    port_raw = os.getenv("SMTP_PORT", "587").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME", "SmartTask").strip() or "SmartTask"

    if not host or not user or not password:
        log.warning("SMTP belum dikonfigurasi. Email ke %s tidak dikirim.", user or "-")
        return None

    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    return host, port, user, password, from_name


def _resolve_ipv4(host: str) -> str:
    try:
        infos = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        if infos:
            return infos[0][4][0]
    except OSError:
        pass
    return host


def _send_email(to_email: str, subject: str, body: str) -> bool:
    cfg = _get_smtp_config()
    if cfg is None:
        return False

    host, port, user, password, from_name = cfg
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{user}>"
    msg["To"] = to_email
    msg.set_content(body)

    target_host = _resolve_ipv4(host)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(target_host, port, timeout=15) as server:
                server.ehlo(host)
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(target_host, port, timeout=15) as server:
                server.ehlo(host)
                server.starttls()
                server.ehlo(host)
                server.login(user, password)
                server.send_message(msg)
        return True
    except Exception as exc:
        log.error("Gagal mengirim email ke %s: %s", to_email, exc)
        return False


def send_verification_otp(to_email: str, otp_code: str) -> bool:
    subject = "Kode Verifikasi OTP SmartTask"
    body = (
        "Halo,\n\n"
        f"Kode verifikasi OTP akun SmartTask Anda adalah: {otp_code}\n"
        "Kode ini berlaku selama 15 menit. Jangan bagikan kode ini kepada siapa pun.\n\n"
        "Salam,\n"
        "SmartTask"
    )
    return _send_email(to_email, subject, body)


def send_task_reminder(
    to_email: str,
    user_name: str,
    task_title: str,
    deadline_text: str,
    course_name: str | None = None,
) -> bool:
    course_line = f"Mata Kuliah : {course_name}\n" if course_name else ""
    subject = f"Pengingat Tugas SmartTask: {task_title}"
    body = (
        f"Halo {user_name or 'Pengguna'},\n\n"
        "Tugas Anda mendekati batas waktu:\n"
        f"Tugas      : {task_title}\n"
        f"{course_line}"
        f"Deadline   : {deadline_text}\n\n"
        "Silakan cek aplikasi SmartTask Anda.\n\n"
        "Salam,\n"
        "SmartTask"
    )
    return _send_email(to_email, subject, body)
