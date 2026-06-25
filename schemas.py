from pydantic import BaseModel
class UserCreate(BaseModel):
    username:str
    password:str

class LoginRequest(BaseModel):
    username:str
    password:str

class OTPVerifyRequest(BaseModel):
    username:str
    otp_code:str