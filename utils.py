from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
import bcrypt

SECRET_KEY = "supersecretkey"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Token generation with expiry (default 10 minutes)
def generate_token(data: dict, expires_sec=600):
    return serializer.dumps(data)

def verify_token(token: str, max_age=600):
    try:
        return serializer.loads(token, max_age=max_age)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Token expired")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid token")

def send_email(recipient: str, link: str):
    msg = MIMEText(f"Click here to verify your account: {link}")
    msg["Subject"] = "Email Verification"
    msg["From"] = "noreply@example.com"
    msg["To"] = recipient

    with smtplib.SMTP("localhost") as server:
        server.sendmail("noreply@example.com", recipient, msg.as_string())

# Bcrypt helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
