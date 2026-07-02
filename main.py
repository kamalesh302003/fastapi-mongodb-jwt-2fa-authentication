from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
from functools import partial
import auth
from database import users_collection
from email_config import send_verification_email, generate_email_otp, otp_expiry
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# helper — run blocking smtplib in thread pool so FastAPI stays async
async def send_email_async(to_email: str, otp: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(_send_email_sync, to_email, otp))


def _send_email_sync(to_email: str, otp: str):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email_config import MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_FROM_NAME, SMTP_SERVER, SMTP_PORT

    html_body = f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:480px;margin:auto;
                background:#1e2536;border-radius:12px;padding:2rem;color:#cdd5e0;">
        <h2 style="color:#5b8dee;text-align:center;">Email Verification</h2>
        <p style="color:#8896a9;text-align:center;">
            Your verification code (expires in 10 minutes):
        </p>
        <div style="margin:1.5rem 0;text-align:center;">
            <span style="font-size:2.5rem;font-weight:700;letter-spacing:0.4em;
                         color:#fff;background:#252d3d;padding:0.8rem 1.5rem;
                         border-radius:10px;">
                {otp}
            </span>
        </div>
        <p style="color:#4a5568;font-size:0.78rem;text-align:center;">
            SecureApp &middot; Two-Factor Auth System
        </p>
    </div>
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Email Verification Code"
    msg["From"]    = f"{MAIL_FROM_NAME} <{MAIL_FROM}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_FROM, to_email, msg.as_string())
    print(f">>> Email sent to {to_email}")


# ---------------- HOME ----------------
@app.get("/home")
async def home():
    return {"message": "Welcome to Two-Factor Authentication System"}


# ---------------- PAGES ----------------
@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.get("/verify-otp", response_class=HTMLResponse)
async def otp_page(request: Request, username: str = ""):
    return templates.TemplateResponse(request, "verify_otp.html", {"username": username})


@app.get("/verify-email-page", response_class=HTMLResponse)
async def verify_email_page(request: Request, username: str = ""):
    return templates.TemplateResponse(request, "verify_email.html", {"username": username})


# ---------------- REGISTER ----------------
@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    existing = await users_collection.find_one({"username": username})
    if existing:
        return templates.TemplateResponse(
            request, "register.html",
            {"error": "Username already exists"}
        )

    otp    = generate_email_otp()
    expiry = otp_expiry()

    user_doc = {
        "username":          username,
        "hashed_password":   auth.hash_password(password),
        "otp_secret":        None,
        "is_2fa_enabled":    False,
        "is_email_verified": False,
        "email_otp":         otp,
        "email_otp_expiry":  expiry
    }
    await users_collection.insert_one(user_doc)

    # Send email
    try:
        await send_email_async(username, otp)
    except Exception as e:
        print(f"Email error: {e}")
        return templates.TemplateResponse(
            request, "register.html",
            {"error": f"Registered but email failed: {e}. Check your email_config.py settings."}
        )

    return RedirectResponse(url=f"/verify-email-page?username={username}", status_code=303)


# ---------------- VERIFY EMAIL ----------------
@app.post("/verify-email")
async def verify_email(
    request: Request,
    username: str = Form(...),
    otp_code: str = Form(...)
):
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_email_verified"):
        return RedirectResponse(url="/login", status_code=303)

    if user.get("email_otp") != otp_code:
        return templates.TemplateResponse(
            request, "verify_email.html",
            {"username": username, "error": "Invalid verification code. Try again."}
        )

    expiry = user.get("email_otp_expiry")
    if expiry and datetime.utcnow() > expiry:
        return templates.TemplateResponse(
            request, "verify_email.html",
            {"username": username, "error": "Code has expired. Click Resend code."}
        )

    await users_collection.update_one(
        {"username": username},
        {
            "$set":   {"is_email_verified": True},
            "$unset": {"email_otp": "", "email_otp_expiry": ""}
        }
    )
    return RedirectResponse(url="/login", status_code=303)


# ---------------- RESEND EMAIL OTP ----------------
@app.get("/resend-email-otp")
async def resend_email_otp(request: Request, username: str = ""):
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_email_verified"):
        return RedirectResponse(url="/login", status_code=303)

    otp    = generate_email_otp()
    expiry = otp_expiry()

    await users_collection.update_one(
        {"username": username},
        {"$set": {"email_otp": otp, "email_otp_expiry": expiry}}
    )

    try:
        await send_email_async(username, otp)
    except Exception as e:
        return templates.TemplateResponse(
            request, "verify_email.html",
            {"username": username, "error": f"Email send failed: {e}"}
        )

    return templates.TemplateResponse(
        request, "verify_email.html",
        {"username": username, "success": "New verification code sent to your email."}
    )


# ---------------- LOGIN ----------------
@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = await users_collection.find_one({"username": username})

    if not user or not auth.verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Invalid username or password"}
        )

    # Block if email not verified
    if not user.get("is_email_verified"):
        return templates.TemplateResponse(
            request, "login.html",
            {
                "error": "Please verify your email first.",
                "resend_url": f"/resend-email-otp?username={username}"
            }
        )

    if user.get("is_2fa_enabled"):
        return RedirectResponse(url=f"/verify-otp?username={username}", status_code=303)

    return RedirectResponse(url=f"/2fa/setup/{username}", status_code=303)


# ---------------- VERIFY TOTP (Login) ----------------
@app.post("/login/verify-otp")
async def verify_otp_login(
    request: Request,
    username: str = Form(...),
    otp_code: str = Form(...)
):
    user = await users_collection.find_one({"username": username})

    if not user or not user.get("is_2fa_enabled") or not user.get("otp_secret"):
        return templates.TemplateResponse(
            request, "verify_otp.html",
            {"username": username, "error": "2FA not enabled for this user"}
        )

    if not auth.verify_otp(user["otp_secret"], otp_code):
        return templates.TemplateResponse(
            request, "verify_otp.html",
            {"username": username, "error": "Invalid OTP code. Try again."}
        )

    token    = auth.create_access_token(username)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True,
                        samesite="lax", secure=False, max_age=1800)
    return response


# ---------------- 2FA SETUP ----------------
@app.get("/2fa/setup/{username}", response_class=HTMLResponse)
async def setup_2fa_page(request: Request, username: str):
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.get("otp_secret"):
        secret = auth.generate_otp_secret()
        await users_collection.update_one(
            {"username": username},
            {"$set": {"otp_secret": secret, "is_2fa_enabled": False}}
        )
    else:
        secret = user["otp_secret"]

    qr_base64 = auth.generate_qr_code(username, secret)
    return templates.TemplateResponse(
        request, "setup_2fa.html",
        {"username": username, "secret": secret, "qr_code": qr_base64}
    )


# ---------------- ENABLE 2FA ----------------
@app.post("/2fa/enable")
async def enable_2fa(
    request: Request,
    username: str = Form(...),
    otp_code: str = Form(...)
):
    user = await users_collection.find_one({"username": username})
    if not user or not user.get("otp_secret"):
        raise HTTPException(status_code=400, detail="2FA setup not initiated")

    if not auth.verify_otp(user["otp_secret"], otp_code):
        qr_base64 = auth.generate_qr_code(username, user["otp_secret"])
        return templates.TemplateResponse(
            request, "setup_2fa.html",
            {
                "username":  username,
                "secret":    user["otp_secret"],
                "qr_code":   qr_base64,
                "error":     "Invalid OTP code. Try again."
            }
        )

    await users_collection.update_one(
        {"username": username},
        {"$set": {"is_2fa_enabled": True}}
    )
    return RedirectResponse(url="/dashboard", status_code=302)


# ---------------- DISABLE 2FA ----------------
@app.post("/2fa/disable")
async def disable_2fa(username: str = Form(...), otp_code: str = Form(...)):
    user = await users_collection.find_one({"username": username})
    if not user or not user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not auth.verify_otp(user["otp_secret"], otp_code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")
    await users_collection.update_one(
        {"username": username},
        {"$set": {"is_2fa_enabled": False, "otp_secret": None}}
    )
    return {"message": "2FA disabled successfully"}


# ---------------- DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    payload = auth.decode_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request, "dashboard.html",
        {"username": payload["sub"]}
    )


# ---------------- LOGOUT ----------------
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response