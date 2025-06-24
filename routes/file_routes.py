from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil, os
from database import get_connection
from utils import generate_token, verify_token

router = APIRouter()
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload")
def upload_file(user_id: int, file: UploadFile = File(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user or user["role"] != "ops":
        raise HTTPException(status_code=403, detail="Only Ops users can upload")
    if not file.filename.endswith((".pptx", ".docx", ".xlsx")):
        raise HTTPException(status_code=400, detail="File type not allowed")

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cursor.execute("INSERT INTO files (filename, path, owner_id) VALUES (?, ?, ?)",
                   (file.filename, path, user["id"]))
    conn.commit()
    conn.close()
    return {"message": "File uploaded successfully"}

@router.get("/files")
def list_files():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files")
    files = cursor.fetchall()
    conn.close()
    return [dict(row) for row in files]

@router.get("/download-file/{file_id}")
def generate_download_link(file_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user or user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can download")
    token = generate_token({"file_id": file_id, "user_id": user_id})
    return {"download-link": f"/download-secure/{token}", "message": "success"}

@router.get("/download-secure/{token}")
def download_file(token: str):
    data = verify_token(token)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (data["user_id"],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM files WHERE id = ?", (data["file_id"],))
    file = cursor.fetchone()
    conn.close()
    if not user or user["role"] != "client":
        raise HTTPException(status_code=403, detail="Access denied")
    return {"filename": file["filename"], "path": file["path"]}
