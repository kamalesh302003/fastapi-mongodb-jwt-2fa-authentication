from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import auth
from database import users_collection

app=FastAPI()
app.mount("/static",StaticFiles(directory="static"),name="static")
templates=Jinja2Templates(directory="templates")

# ---------------- HOME ----------------
@app.get("/home")
async def home():
    return {"message":"Welcome to Two-Factor Authentication System"}

# ---------------- LOGIN PAGE ----------------
@app.get("/",response_class=HTMLResponse)
async def root_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

@app.get("/login",response_class=HTMLResponse)
async def login_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

# ---------------- REGISTER PAGE ----------------
@app.get("/register",response_class=HTMLResponse)
async def register_page(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})

# ---------------- OTP PAGE ----------------
@app.get("/verify-otp",response_class=HTMLResponse)
async def otp_page(request:Request,username:str=""):
    return templates.TemplateResponse(
        "verify_otp.html",
        {"request":request,"username":username}
    )

# ---------------- REGISTER ----------------
@app.post("/register")
async def register(
    request:Request,
    username:str=Form(...),
    password:str=Form(...)
):
    existing=await users_collection.find_one({"username":username})
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request":request,"error":"Username already exists"}
        )

    user_doc={
        "username":username,
        "hashed_password":auth.hash_password(password),
        "otp_secret":None,
        "is_2fa_enabled":False
    }
    await users_collection.insert_one(user_doc)
    return RedirectResponse(url="/login",status_code=303)

# ---------------- LOGIN ----------------
@app.post("/login")
async def login(
    request:Request,
    username:str=Form(...),
    password:str=Form(...)
):
    user=await users_collection.find_one({"username":username})

    if not user or not auth.verify_password(password,user["hashed_password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request":request,"error":"Invalid username or password"}
        )

    if user.get("is_2fa_enabled"):
        # 2FA already enabled → ask for OTP code
        return RedirectResponse(
            url=f"/verify-otp?username={username}",
            status_code=303
        )

    # 2FA not yet enabled → go to setup QR code page
    return RedirectResponse(
        url=f"/2fa/setup/{username}",  # ← changed from /dashboard
        status_code=303
    )

# ---------------- VERIFY OTP (Login) ----------------
@app.post("/login/verify-otp")
async def verify_otp_login(
    request:Request,
    username:str=Form(...),
    otp_code:str=Form(...)
):
    user=await users_collection.find_one({"username":username})

    if not user or not user.get("is_2fa_enabled") or not user.get("otp_secret"):
        return templates.TemplateResponse(
            "verify_otp.html",
            {"request":request,"username":username,"error":"2FA not enabled for this user"}
        )

    if not auth.verify_otp(user["otp_secret"],otp_code):
        return templates.TemplateResponse(
            "verify_otp.html",
            {"request":request,"username":username,"error":"Invalid OTP code.Try again."}
        )

    token=auth.create_access_token(username)
    response=RedirectResponse(url="/dashboard",status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=1800
    )
    return response

# ---------------- 2FA SETUP PAGE (GET) ----------------
@app.get("/2fa/setup/{username}",response_class=HTMLResponse)
async def setup_2fa_page(request:Request,username:str):
    user=await users_collection.find_one({"username":username})
    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    # Only generate new secret if one doesn't exist
    if not user.get("otp_secret"):
        secret=auth.generate_otp_secret()
        await users_collection.update_one(
            {"username":username},
            {"$set":{"otp_secret":secret,"is_2fa_enabled":False}}
        )
    else:
        secret=user["otp_secret"]
    qr_base64=auth.generate_qr_code(username,secret)
    return templates.TemplateResponse(
        "setup_2fa.html",
        {
            "request":request,
            "username":username,
            "secret":secret,
            "qr_code":qr_base64
        }
    )

# ---------------- ENABLE 2FA ----------------
@app.post("/2fa/enable")
async def enable_2fa(
    request:Request,
    username:str=Form(...),
    otp_code:str=Form(...)
):
    user=await users_collection.find_one({"username":username})

    if not user or not user.get("otp_secret"):
        raise HTTPException(status_code=400,detail="2FA setup not initiated")

    # Debug prints — check your terminal when you submit
    import pyotp
    totp=pyotp.TOTP(user["otp_secret"])
    print(f"\n>>> Username:{username}")
    print(f">>> Secret:{user['otp_secret']}")
    print(f">>> Code entered:{otp_code}")
    print(f">>> Expected code:{totp.now()}\n")
    if not auth.verify_otp(user["otp_secret"],otp_code):
        qr_base64=auth.generate_qr_code(username,user["otp_secret"])
        return templates.TemplateResponse(
            "setup_2fa.html",
            {
                "request":request,
                "username":username,
                "secret":user["otp_secret"],
                "qr_code":qr_base64,
                "error":"Invalid OTP code.Try again."
            }
        )
    await users_collection.update_one(
        {"username":username},
        {"$set":{"is_2fa_enabled":True}}
    )
    print(f">>> 2FA ENABLED for {username}")
    return RedirectResponse(url="/dashboard",status_code=302)

# ---------------- DISABLE 2FA ----------------
@app.post("/2fa/disable")
async def disable_2fa(
    username:str=Form(...),
    otp_code:str=Form(...)
):
    user=await users_collection.find_one({"username":username})
    if not user or not user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400,detail="2FA is not enabled")

    if not auth.verify_otp(user["otp_secret"],otp_code):
        raise HTTPException(status_code=401,detail="Invalid OTP code")

    await users_collection.update_one(
        {"username":username},
        {"$set":{"is_2fa_enabled":False,"otp_secret":None}}
    )
    return {"message":"2FA disabled successfully"}

# ---------------- DASHBOARD ----------------
@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard(request:Request):
    token=request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login",status_code=303)
    payload=auth.decode_token(token)
    if not payload:
        return RedirectResponse(url="/login",status_code=303)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request":request,"username":payload["sub"]}
    )

# ---------------- LOGOUT ----------------
@app.get("/logout")
async def logout():
    response=RedirectResponse(url="/login",status_code=303)
    response.delete_cookie("access_token")
    return response