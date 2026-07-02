# 🔐 FastAPI Authentication System with Email Verification & Two-Factor Authentication

A secure authentication system built using **FastAPI**, **MongoDB**, **JWT**, **Email Verification**, and **Two-Factor Authentication (2FA)**. This project demonstrates a production-inspired authentication workflow with email verification, password hashing, QR code generation, Google Authenticator integration, OTP verification, and protected dashboard access.

---

## 🚀 Features

- ✅ User Registration
- ✅ Email Verification
- ✅ Secure Password Hashing
- ✅ User Login
- ✅ JWT Authentication
- ✅ Cookie-Based Session Management
- ✅ Two-Factor Authentication (2FA)
- ✅ Google Authenticator Integration
- ✅ QR Code Generation
- ✅ OTP Verification
- ✅ Protected Dashboard
- ✅ Logout Functionality
- ✅ MongoDB Integration
- ✅ Jinja2 Template Rendering
- ✅ FastAPI RESTful API

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- JWT (JSON Web Token)
- Passlib (Password Hashing)
- PyOTP
- FastAPI-Mail

### Database
- MongoDB
- Motor (Async MongoDB Driver)

### Frontend
- HTML5
- CSS3
- Jinja2 Templates

### Security
- Email Verification
- Password Hashing
- JWT Authentication
- HTTPOnly Cookies
- Time-Based One-Time Passwords (TOTP)
- Google Authenticator

---

# 📂 Project Structure

```text
fastapi-authentication-system/
│
├── main.py
├── auth.py
├── database.py
├── email_service.py
├── email_config.py
├── requirements.txt
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── verify_email.html
│   ├── verify_otp.html
│   ├── setup_2fa.html
│   └── dashboard.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/fastapi-authentication-system.git

cd fastapi-authentication-system
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure MongoDB

Ensure MongoDB is running.

Example:

```python
client = AsyncIOMotorClient("mongodb://localhost:27017")

db = client["authentication_db"]

users_collection = db["users"]
```

---

## Configure Gmail SMTP

Enable **2-Step Verification** on your Google account.

Generate an **App Password**.

Update:

```python
MAIL_USERNAME = "your_email@gmail.com"

MAIL_PASSWORD = "your_app_password"

MAIL_FROM = "your_email@gmail.com"
```

---

# ▶️ Run the Application

```bash
uvicorn main:app --reload
```

Application URL

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

---

# 🔐 Authentication Workflow

```
User Registration
        │
        ▼
Store User in MongoDB
        │
        ▼
Generate Email Verification Token
        │
        ▼
Send Verification Email
        │
        ▼
User Clicks Verification Link
        │
        ▼
Email Verified
        │
        ▼
Login with Username & Password
        │
        ▼
Setup Google Authenticator (First Login)
        │
        ▼
Scan QR Code
        │
        ▼
Verify OTP
        │
        ▼
Enable Two-Factor Authentication
        │
        ▼
Future Login
        │
        ▼
Password Verification
        │
        ▼
OTP Verification
        │
        ▼
JWT Token Created
        │
        ▼
Protected Dashboard
```

---

# 📧 Email Verification

- Verification email sent during registration.
- Secure verification token generated.
- Account remains inactive until email verification.
- Prevents fake or invalid registrations.

---

# 🔑 Two-Factor Authentication

Users can enable 2FA using Google Authenticator.

Supported Apps:

- Google Authenticator
- Microsoft Authenticator
- Authy

Features:

- QR Code Generation
- Secret Key Generation
- OTP Verification
- Enable/Disable 2FA

---

# 🔒 Security Features

- Password Hashing (bcrypt)
- Email Verification
- JWT Authentication
- HTTPOnly Cookies
- OTP Verification
- Google Authenticator Support
- Protected Routes
- Secure Session Management

---

# 📡 API Endpoints

| Method | Endpoint | Description |
|----------|---------------------------|---------------------------|
| GET | / | Login Page |
| GET | /register | Register Page |
| POST | /register | Register User |
| GET | /verify-email/{token} | Verify Email |
| POST | /login | User Login |
| GET | /verify-otp | OTP Page |
| POST | /login/verify-otp | Verify Login OTP |
| GET | /2fa/setup/{username} | Setup 2FA |
| POST | /2fa/enable | Enable 2FA |
| POST | /2fa/disable | Disable 2FA |
| GET | /dashboard | Protected Dashboard |
| GET | /logout | Logout |

---

# 🎯 Learning Outcomes

This project demonstrates:

- FastAPI Development
- REST API Development
- MongoDB Integration
- JWT Authentication
- Email Verification
- Password Hashing
- Google Authenticator Integration
- QR Code Generation
- OTP Verification
- Two-Factor Authentication (2FA)
- Cookie-Based Authentication
- Secure Backend Development

---

# 📈 Future Enhancements

- Password Reset via Email
- Refresh Token Authentication
- Role-Based Access Control (RBAC)
- OAuth Login (Google & GitHub)
- SMS OTP Verification
- Backup Recovery Codes
- Docker Deployment
- HTTPS Configuration
- Account Lockout Protection
- Login Attempt Limiting
- User Profile Management
- Audit Logs

---
- GitHub: https://github.com/kamalesh302003
- LinkedIn: https://www.linkedin.com/in/kamalesh-chandrasekaran-6a881728b
---

# ⭐ Support
If you found this project helpful, consider giving it a ⭐ on GitHub!

Feedback and contributions are always welcome.
