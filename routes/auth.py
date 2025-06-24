from fastapi import APIRouter, HTTPException
from schemas import UserCreate, UserLogin
from database import get_connection
from utils import generate_token, send_email, verify_token, hash_password, verify_password

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = hash_password(user.password)
    cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                   (user.email, hashed_pwd, user.role))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = generate_token({"user_id": user_id})
    verify_url = f"http://localhost:8000/verify-email/{token}"
    send_email(user.email, verify_url)
    return {"message": "Verification email sent", "url": verify_url}

@router.get("/verify-email/{token}")
def verify_email(token: str):
    data = verify_token(token)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (data["user_id"],))
    conn.commit()
    conn.close()
    return {"message": "Email verified"}

@router.post("/login")
def login(user: UserLogin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    result = cursor.fetchone()
    conn.close()
    if not result or not verify_password(user.password, result["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": result["id"], "role": result["role"]}
