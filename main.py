from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/style.css")
def styles():
    return FileResponse("style.css")


class PasswordCheck(BaseModel):
    password:str

@app.post("/check-password")
def check_password(data:PasswordCheck):
    length=len(data.password)
    return{"password_length":length}