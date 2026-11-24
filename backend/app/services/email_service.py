import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SmartTask")


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP belum dikonfigurasi. Email ke %s tidak dikirim.", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as exc:
        logger.error("Gagal mengirim email ke %s: %s", to_email, exc)
        return False


def send_verification_otp(to_email: str, otp_code: str) -> bool:
    subject = f"[{otp_code}] Kode Verifikasi Akun SmartTask"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
      <h2 style="color: #1e293b; margin-top: 0;">Verifikasi Email SmartTask</h2>
      <p>Gunakan kode OTP berikut untuk mengaktifkan akun Anda:</p>
      <div style="font-size: 28px; font-weight: bold; letter-spacing: 6px; text-align: center; padding: 14px; background: #f1f5f9; border-radius: 8px; margin: 16px 0; color: #0f172a;">
        {otp_code}
      </div>
      <p style="color: #64748b; font-size: 13px; margin-bottom: 0;">
        Kode berlaku selama 15 menit. Jika Anda tidak merasa mendaftar, abaikan email ini.
      </p>
    </div>
    """
    return send_email(to_email, subject, html_body)


def send_task_reminder_email(
    to_email: str,
    task_title: str,
    course_name: str,
    deadline_str: str,
    hours_left: int,
) -> bool:
    subject = f"Pengingat Tugas ({hours_left} Jam Lagi): {task_title}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
      <h2 style="color: #2563eb; margin-top: 0;">Pengingat Deadline Tugas</h2>
      <p>Halo, tugas kuliah Anda mendekati batas waktu:</p>
      <table style="width: 100%; border-collapse: collapse; margin: 12px 0;">
        <tr>
          <td style="padding: 6px 0; color: #64748b;">Tugas</td>
          <td style="padding: 6px 0; font-weight: bold;">{task_title}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #64748b;">Mata Kuliah</td>
          <td style="padding: 6px 0;">{course_name or "-"}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; color: #64748b;">Deadline</td>
          <td style="padding: 6px 0; color: #dc2626; font-weight: bold;">{deadline_str}</td>
        </tr>
      </table>
      <p style="color: #475569; font-size: 13px; margin-bottom: 0;">
        Buka SmartTask untuk memperbarui status tugas jika sudah selesai.
      </p>
    </div>
    """
    return send_email(to_email, subject, html_body)