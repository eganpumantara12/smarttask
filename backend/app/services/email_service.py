import json
import logging
import os
import smtplib
import socket
from email.message import EmailMessage
from urllib import error, request

from app.services.email_templates import build_deadline_reminder_email, build_otp_email

log = logging.getLogger("app.services.email_service")


def _send_via_resend(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        return False

    from_name = os.getenv("SMTP_FROM_NAME", "SmartTask").strip() or "SmartTask"
    from_email = (
        os.getenv("EMAIL_FROM", "").strip()
        or os.getenv("SMTP_USER", "").strip()
        or "onboarding@resend.dev"
    )
    sender = f"{from_name} <{from_email}>" if "<" not in from_email else from_email

    data: dict[str, object] = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }
    if html_body:
        data["html"] = html_body

    payload = json.dumps(data).encode("utf-8")

    req = request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SmartTask/1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            if 200 <= resp.status < 300:
                return True
            log.error("Resend mengembalikan status %s untuk %s", resp.status, to_email)
            return False
    except error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="ignore")
        log.error("Gagal kirim via Resend ke %s (HTTP %s): %s", to_email, exc.code, err_body)
        return False
    except Exception as exc:
        log.error("Gagal kirim via Resend ke %s: %s", to_email, exc)
        return False


def _get_smtp_config() -> tuple[str, int, str, str, str] | None:
    host = os.getenv("SMTP_HOST", "").strip()
    port_raw = os.getenv("SMTP_PORT", "587").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME", "SmartTask").strip() or "SmartTask"

    if not host or not user or not password:
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


def _try_smtp(
    target_host: str, host: str, port: int, user: str, password: str, msg: EmailMessage
) -> None:
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


def _send_email(to_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
    if os.getenv("RESEND_API_KEY", "").strip():
        return _send_via_resend(to_email, subject, body, html_body=html_body)

    cfg = _get_smtp_config()
    if cfg is None:
        log.warning("SMTP dan RESEND_API_KEY belum dikonfigurasi. Email ke %s tidak dikirim.", to_email)
        return False

    host, port, user, password, from_name = cfg
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{user}>"
    msg["To"] = to_email
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    target_host = _resolve_ipv4(host)
    ports_to_try = [port] + ([465] if port != 465 else [587])

    last_exc: Exception | None = None
    for p in ports_to_try:
        try:
            _try_smtp(target_host, host, p, user, password, msg)
            return True
        except Exception as exc:
            last_exc = exc
            log.warning("Percobaan SMTP ke %s:%s gagal (%s), mencoba jalur alternatif...", host, p, exc)

    log.error("Gagal mengirim email ke %s: %s", to_email, last_exc)
    return False


def send_verification_otp(to_email: str, otp_code: str) -> bool:
    expires_minutes = 15
    subject = "Kode Verifikasi OTP SmartTask"
    html_body, text_body = build_otp_email(otp_code=otp_code, expires_minutes=expires_minutes)
    return _send_email(to_email, subject, text_body, html_body=html_body)


def send_task_reminder(
    to_email: str,
    user_name: str,
    task_title: str,
    deadline_text: str,
    course_name: str | None = None,
) -> bool:
    subject = f"Pengingat Tugas SmartTask: {task_title}"
    html_body, text_body = build_deadline_reminder_email(
        task_title=task_title,
        course_name=course_name or "Umum",
        deadline_str=deadline_text,
    )
    return _send_email(to_email, subject, text_body, html_body=html_body)
