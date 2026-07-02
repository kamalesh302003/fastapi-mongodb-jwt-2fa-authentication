import smtplib
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# ── Fill these details ────────────────────────────────────────
MAIL_USERNAME = "ckamalesh433@gmail.com"      # ← your Gmail
MAIL_PASSWORD = "yvmx howq cdca vpao"       # ← Gmail App Password
MAIL_FROM     = "ckamalesh433@gmail.com"      # ← same as username
MAIL_FROM_NAME = "SecureApp"
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587


# ── Generate 6-digit OTP ──────────────────────────────────────
def generate_email_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


# ── OTP expiry: 10 minutes ────────────────────────────────────
def otp_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=10)


# ── Send email using smtplib (no extra package needed) ────────
async def send_verification_email(to_email: str, otp: str):
    html_body = f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:480px;margin:auto;
                background:#1e2536;border-radius:12px;padding:2rem;color:#cdd5e0;">

        <h2 style="color:#5b8dee;margin-bottom:0.5rem;text-align:center;">
            Email Verification
        </h2>

        <p style="color:#8896a9;font-size:0.9rem;text-align:center;">
            Use the code below to verify your email address.<br>
            This code expires in <strong style="color:#e2e8f0;">10 minutes</strong>.
        </p>

        <div style="margin:1.5rem 0;text-align:center;">
            <span style="font-size:2.5rem;font-weight:700;letter-spacing:0.4em;
                         color:#fff;background:#252d3d;padding:0.8rem 1.5rem;
                         border-radius:10px;border:1px solid rgba(91,141,238,0.3);">
                {otp}
            </span>
        </div>

        <p style="color:#4a5568;font-size:0.78rem;text-align:center;">
            If you did not request this, please ignore this email.
        </p>

        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:1.5rem 0;">

        <p style="color:#4a5568;font-size:0.72rem;text-align:center;">
            SecureApp &middot; Two-Factor Auth System
        </p>
    </div>
    """

    # Build email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Email Verification Code"
    msg["From"]    = f"{MAIL_FROM_NAME} <{MAIL_FROM}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(html_body, "html"))

    # Send via Gmail SMTP
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())

    print(f">>> Verification email sent to {to_email}")