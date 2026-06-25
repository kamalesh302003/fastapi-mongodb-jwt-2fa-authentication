import pyotp
import qrcode
import io
import base64
from datetime import datetime,timedelta
from jose import JWTError,jwt
from passlib.context import CryptContext
SECRET_KEY="a1b2c3d4e5f6g7h8i9j0klmnopqrstuvwxyz1234"  # ← change this to a random string
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(username:str):
    to_encode={"sub":username}
    expire=datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token:str):
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except JWTError:
        return None

def generate_otp_secret():
    return pyotp.random_base32()

def generate_qr_code(username:str,secret:str,issuer="MyApp"):
    totp=pyotp.TOTP(secret)
    uri=totp.provisioning_uri(name=username,issuer_name=issuer)
    img=qrcode.make(uri)
    buf=io.BytesIO()
    img.save(buf,format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def verify_otp(secret:str,code:str)->bool:
    totp=pyotp.TOTP(secret)
    return totp.verify(code,valid_window=2)  # ±60 seconds tolerance