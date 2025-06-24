from fastapi import FastAPI
from routes import auth, file_routes
from database import init_db

app = FastAPI()
init_db()

app.include_router(auth.router)
app.include_router(file_routes.router)
