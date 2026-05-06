"""
Sends job results via email using SMTP (Gmail-compatible).
Set EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO in env.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

SMTP_HOST = os.getenv("EMAIL_SMTP_HOST") or "smtp.gmail.com"
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT") or 587)
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASSWORD"].replace(" ", "")  # Gmail app passwords may include spaces
EMAIL_TO   = os.environ["EMAIL_TO"]


def send_email(subject: str, html_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        return True
    except Exception as e:
        print(f"[sender] Email error: {e}")
        return False


def send_jobs(jobs: list[dict], total: int) -> None:
    from formatter import build_html_email
    subject  = f"🔍 {total} New Job Match{'es' if total != 1 else ''} — Job Search Pipeline"
    html     = build_html_email(jobs)
    ok       = send_email(subject, html)
    if ok:
        print(f"[sender] Email sent to {EMAIL_TO}")
    else:
        raise RuntimeError("Failed to send email")


def send_notice(message: str) -> None:
    send_email("Job Search Pipeline — Notice", f"<p>{message}</p>")
