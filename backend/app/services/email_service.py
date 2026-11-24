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


def _try_send(target_host: str, host: str, port: int, user: str, password: str, msg: EmailMessage) -> None:
    if port == 465:
        with smtplib.SMTP_SSL(target_host, 465, timeout=12) as server:
            server.ehlo(host)
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(target_host, port, timeout=12) as server:
            server.ehlo(host)
            server.starttls()
            server.ehlo(host)
            server.login(user, password)
            server.send_message(msg)


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
    ports_to_try = [port] + ([465] if port != 465 else [587])

    last_exc: Exception | None = None
    for p in ports_to_try:
        try:
            _try_send(target_host, host, p, user, password, msg)
            return True
        except Exception as exc:
            last_exc = exc
            log.warning("Percobaan SMTP ke %s:%s gagal (%s), mencoba jalur alternatif...", host, p, exc)

    log.error("Gagal mengirim email ke %s: %s", to_email, last_exc)
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
