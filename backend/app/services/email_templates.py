def build_otp_email(otp_code: str, expires_minutes: int = 10) -> tuple[str, str]:
    subject = f"{otp_code} adalah kode verifikasi SmartTask Anda"

    html = f"""
    <!DOCTYPE html>
    <html lang="id">
      <body style="margin:0; padding:24px; background-color:#f4f5f9; font-family:Arial, Helvetica, sans-serif; color:#1e293b;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          <tr>
            <td align="center">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:480px; background-color:#ffffff; border-radius:12px; padding:32px; border:1px solid #e2e8f0;">
                <tr>
                  <td style="padding-bottom:16px;">
                    <span style="font-size:18px; font-weight:700; color:#4f46e5;">SmartTask</span>
                  </td>
                </tr>
                <tr>
                  <td style="font-size:20px; font-weight:700; padding-bottom:8px; color:#0f172a;">
                    Kode Verifikasi OTP
                  </td>
                </tr>
                <tr>
                  <td style="font-size:14px; line-height:1.6; color:#475569; padding-bottom:24px;">
                    Gunakan kode berikut untuk melanjutkan proses di <strong>SmartTask</strong>. Kode berlaku selama <strong>{expires_minutes} menit</strong>.
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom:24px;">
                    <div style="display:inline-block; padding:14px 28px; background-color:#eef2ff; border:1px solid #c7d2fe; border-radius:8px; font-size:28px; font-weight:700; letter-spacing:8px; color:#3730a3;">
                      {otp_code}
                    </div>
                  </td>
                </tr>
                <tr>
                  <td style="font-size:12px; line-height:1.6; color:#64748b; border-top:1px solid #f1f5f9; padding-top:16px;">
                    Jika Anda tidak merasa meminta kode ini, abaikan saja email ini.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    text = (
        f"{subject}\n\n"
        f"Gunakan kode berikut untuk melanjutkan di SmartTask: {otp_code}\n"
        f"Kode berlaku selama {expires_minutes} menit.\n"
        f"Jika Anda tidak merasa meminta kode ini, abaikan email ini."
    )

    return html, text


def build_deadline_reminder_email(
    task_title: str,
    course_name: str,
    deadline_str: str,
    app_url: str = "https://app.smart-task.my.id",
) -> tuple[str, str]:
    subject = f"Pengingat Deadline: {task_title}"

    html = f"""
    <!DOCTYPE html>
    <html lang="id">
      <body style="margin:0; padding:24px; background-color:#f4f5f9; font-family:Arial, Helvetica, sans-serif; color:#1e293b;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          <tr>
            <td align="center">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:480px; background-color:#ffffff; border-radius:12px; padding:32px; border:1px solid #e2e8f0;">
                <tr>
                  <td style="padding-bottom:16px;">
                    <span style="font-size:18px; font-weight:700; color:#4f46e5;">SmartTask</span>
                  </td>
                </tr>
                <tr>
                  <td style="font-size:20px; font-weight:700; padding-bottom:8px; color:#0f172a;">
                    Tugas Mendekati Deadline
                  </td>
                </tr>
                <tr>
                  <td style="font-size:14px; line-height:1.6; color:#475569; padding-bottom:20px;">
                    Jangan lupa selesaikan tugas berikut sebelum tenggat waktunya:
                  </td>
                </tr>
                <tr>
                  <td style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:24px;">
                    <div style="font-size:15px; font-weight:700; color:#0f172a; margin-bottom:6px;">{task_title}</div>
                    <div style="font-size:13px; color:#475569; margin-bottom:4px;">Mata Kuliah: <strong>{course_name}</strong></div>
                    <div style="font-size:13px; color:#b91c1c;">Deadline: <strong>{deadline_str}</strong></div>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top:24px; padding-bottom:20px;">
                    <a href="{app_url}" style="display:inline-block; background-color:#4f46e5; color:#ffffff; text-decoration:none; font-size:14px; font-weight:600; padding:12px 24px; border-radius:8px;">
                      Buka SmartTask
                    </a>
                  </td>
                </tr>
                <tr>
                  <td style="font-size:12px; line-height:1.6; color:#64748b; border-top:1px solid #f1f5f9; padding-top:16px;">
                    Email otomatis dari SmartTask ({app_url}).
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    text = (
        f"{subject}\n\n"
        f"Tugas: {task_title}\n"
        f"Mata Kuliah: {course_name}\n"
        f"Deadline: {deadline_str}\n\n"
        f"Buka SmartTask: {app_url}"
    )

    return html, text
